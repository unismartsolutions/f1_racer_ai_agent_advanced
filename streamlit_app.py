import streamlit as st
import os
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Import our modules
from f1_agent_langchain import F1RacerAgent, RaceStage, SessionType, RaceResult
from auth import authenticate_user, check_authentication
from config import get_config

# Configure page
st.set_page_config(
    page_title="F1 Racer AI Agent",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'context_configured' not in st.session_state:
        st.session_state.context_configured = False
    if 'interaction_history' not in st.session_state:
        st.session_state.interaction_history = []

def login_page():
    """Display login page"""
    st.title("🏎️ F1 Racer AI Agent")
    st.subheader("Please login to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        # Demo credentials info
        st.info("""
        **Demo Credentials:**
        - Username: `admin` / Password: `f1racing2024`
        - Username: `driver` / Password: `speedster123`
        - Username: `fan` / Password: `motorsport`
        """)

def logout():
    """Handle logout"""
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.agent = None
    st.session_state.context_configured = False
    st.session_state.interaction_history = []
    st.rerun()

def context_config_tab():
    """Context configuration tab"""
    st.header("🏁 Context Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Driver & Team")
        racer_name = st.text_input("Racer Name", value="Lightning McQueen")
        team_name = st.text_input("Team Name", value="Rusteze Racing")
        
        st.subheader("Race Weekend")
        stage = st.selectbox(
            "Race Stage",
            options=[RaceStage.PRACTICE, RaceStage.QUALIFYING, RaceStage.RACE, RaceStage.POST_RACE],
            format_func=lambda x: x.value.title(),
            index=0
        )
        
        session_type = None
        if stage in [RaceStage.PRACTICE, RaceStage.QUALIFYING]:
            session_options = [SessionType.FP1, SessionType.FP2, SessionType.FP3, 
                             SessionType.Q1, SessionType.Q2, SessionType.Q3, SessionType.RACE]
            session_type = st.selectbox(
                "Session Type",
                options=session_options,
                format_func=lambda x: x.value,
                index=0
            )
    
    with col2:
        st.subheader("Circuit & Race")
        circuit_name = st.text_input("Circuit Name", value="Nurburgring")
        race_name = st.text_input("Race Name", value="German Grand Prix")
        
        st.subheader("Performance Context")
        last_result = None
        position = None
        
        if stage == RaceStage.POST_RACE:
            result_options = [RaceResult.WIN, RaceResult.PODIUM, RaceResult.POINTS,
                            RaceResult.DNF, RaceResult.CRASH, RaceResult.DISAPPOINTING]
            last_result = st.selectbox(
                "Last Result",
                options=result_options,
                format_func=lambda x: x.value.title(),
                index=0
            )
            
            if last_result in [RaceResult.WIN, RaceResult.PODIUM, RaceResult.POINTS]:
                position = st.number_input("Finishing Position", min_value=1, max_value=20, value=1)
        
        mood_options = ["excited", "confident", "disappointed", "focused", "neutral", "frustrated"]
        mood = st.selectbox("Agent Mood", options=mood_options, index=4)
    
    if st.button("🚀 Configure Agent", type="primary"):
        try:
            with st.spinner("Configuring F1 Agent..."):
                # Create or update agent
                if st.session_state.agent is None:
                    st.session_state.agent = F1RacerAgent(racer_name, team_name)
                else:
                    st.session_state.agent.racer_name = racer_name
                    st.session_state.agent.team_name = team_name
                
                # Update context
                st.session_state.agent.update_context(
                    stage=stage,
                    session_type=session_type,
                    circuit_name=circuit_name,
                    race_name=race_name,
                    last_result=last_result,
                    position=position,
                    mood=mood
                )
                
                st.session_state.context_configured = True
                st.success("✅ Agent configured successfully!")
                
                # Display current configuration
                st.subheader("Current Configuration")
                config_info = st.session_state.agent.get_agent_info()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Driver", config_info['racer_name'])
                    st.metric("Team", config_info['team_name'])
                
                with col2:
                    st.metric("Stage", config_info['current_stage'].title())
                    if config_info['session_type']:
                        st.metric("Session", config_info['session_type'])
                
                with col3:
                    st.metric("Circuit", config_info['circuit'])
                    st.metric("Mood", config_info['mood'].title())
                
        except Exception as e:
            st.error(f"Error configuring agent: {str(e)}")

def agent_interaction_tab():
    """Agent interaction tab"""
    if not st.session_state.context_configured:
        st.warning("⚠️ Please configure the agent context first!")
        return
    
    st.header("🏎️ Agent Interaction")
    
    # Interaction type selection
    interaction_types = {
        "Generate Status Post": "post",
        "Reply to Fan Comment": "reply",
        "Mention Teammate/Competitor": "mention",
        "Simulate Like Action": "like",
        "View Agent Thoughts": "thoughts"
    }
    
    selected_interaction = st.selectbox(
        "Select Interaction Type",
        options=list(interaction_types.keys())
    )
    
    interaction_type = interaction_types[selected_interaction]
    
    # Handle different interaction types
    if interaction_type == "post":
        handle_status_post()
    elif interaction_type == "reply":
        handle_fan_reply()
    elif interaction_type == "mention":
        handle_mention()
    elif interaction_type == "like":
        handle_like_simulation()
    elif interaction_type == "thoughts":
        handle_agent_thoughts()
    
    # Display interaction history
    if st.session_state.interaction_history:
        st.subheader("📜 Interaction History")
        for i, interaction in enumerate(reversed(st.session_state.interaction_history[-10:])):
            with st.expander(f"{interaction['type']} - {interaction['timestamp'].strftime('%H:%M:%S')}"):
                st.write(f"**Input:** {interaction.get('input', 'N/A')}")
                st.write(f"**Output:** {interaction['output']}")

def handle_status_post():
    """Handle status post generation"""
    st.subheader("📱 Generate Status Post")
    
    post_types = {
        "General": "general",
        "Victory Celebration": "win",
        "Podium Finish": "podium",
        "Disappointing Result": "disappointing",
        "Practice Session": "practice",
        "Qualifying": "qualifying"
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_post_type = st.selectbox("Post Type", options=list(post_types.keys()))
        post_type = post_types[selected_post_type]
    
    with col2:
        if st.button("🚀 Generate Post", type="primary"):
            try:
                with st.spinner("Generating post..."):
                    post = st.session_state.agent.speak(post_type)
                    
                    st.success("✅ Post generated!")
                    st.text_area("Generated Post", value=post, height=150, disabled=True)
                    
                    # Add to history
                    st.session_state.interaction_history.append({
                        'type': 'Status Post',
                        'input': selected_post_type,
                        'output': post,
                        'timestamp': datetime.now()
                    })
                    
            except Exception as e:
                st.error(f"Error generating post: {str(e)}")

def handle_fan_reply():
    """Handle fan comment reply"""
    st.subheader("💬 Reply to Fan Comment")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fan_comment = st.text_area("Fan Comment", placeholder="Enter the fan comment here...")
        
        # Sample comments for testing
        sample_comments = [
            "Amazing drive today! You were flying out there!",
            "Tough luck with the result, but we believe in you!",
            "What's your favorite part about racing at this circuit?",
            "Keep pushing! The championship is still possible!",
            "That overtake was absolutely brilliant!"
        ]
        
        selected_sample = st.selectbox("Or choose a sample comment:", 
                                     options=[""] + sample_comments)
        if selected_sample:
            fan_comment = selected_sample
    
    with col2:
        if st.button("💭 Generate Reply", type="primary"):
            if fan_comment.strip():
                try:
                    with st.spinner("Generating reply..."):
                        reply = st.session_state.agent.reply_to_comment(fan_comment)
                        
                        st.success("✅ Reply generated!")
                        
                        # Display in a nice format
                        st.markdown("**Fan Comment:**")
                        st.info(fan_comment)
                        st.markdown("**Agent Reply:**")
                        st.success(reply)
                        
                        # Add to history
                        st.session_state.interaction_history.append({
                            'type': 'Fan Reply',
                            'input': fan_comment,
                            'output': reply,
                            'timestamp': datetime.now()
                        })
                        
                except Exception as e:
                    st.error(f"Error generating reply: {str(e)}")
            else:
                st.warning("Please enter a fan comment first!")

def handle_mention():
    """Handle mention generation"""
    st.subheader("🏷️ Mention Teammate/Competitor")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        person_name = st.text_input("Person's Name", placeholder="e.g., Max Verstappen")
    
    with col2:
        mention_contexts = {
            "Positive": "positive",
            "Teammate": "teammate", 
            "Competitive": "competitive"
        }
        selected_context = st.selectbox("Mention Context", options=list(mention_contexts.keys()))
        mention_context = mention_contexts[selected_context]
    
    with col3:
        if st.button("🎯 Generate Mention", type="primary"):
            if person_name.strip():
                try:
                    with st.spinner("Generating mention..."):
                        mention = st.session_state.agent.mention_teammate_or_competitor(person_name, mention_context)
                        
                        st.success("✅ Mention generated!")
                        st.text_area("Generated Mention", value=mention, height=100, disabled=True)
                        
                        # Add to history
                        st.session_state.interaction_history.append({
                            'type': 'Mention',
                            'input': f"{person_name} ({selected_context})",
                            'output': mention,
                            'timestamp': datetime.now()
                        })
                        
                except Exception as e:
                    st.error(f"Error generating mention: {str(e)}")
            else:
                st.warning("Please enter a person's name first!")

def handle_like_simulation():
    """Handle like action simulation"""
    st.subheader("👍 Simulate Like Action")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        post_content = st.text_area("Post Content to Like", placeholder="Enter the post content here...")
        
        # Sample posts for testing
        sample_posts = [
            "Great race weekend everyone! Thanks for the amazing support!",
            "Working hard in the garage to find those extra tenths",
            "Ready for tomorrow's qualifying session! 🏁",
            "Huge congratulations to the whole team for this victory!",
            "Tough day at the office but we'll come back stronger"
        ]
        
        selected_sample = st.selectbox("Or choose a sample post:", 
                                     options=[""] + sample_posts)
        if selected_sample:
            post_content = selected_sample
    
    with col2:
        if st.button("❤️ Simulate Like", type="primary"):
            if post_content.strip():
                try:
                    with st.spinner("Analyzing post..."):
                        like_action = st.session_state.agent.simulate_like_action(post_content)
                        
                        st.success("✅ Like action simulated!")
                        st.info(like_action)
                        
                        # Add to history
                        st.session_state.interaction_history.append({
                            'type': 'Like Action',
                            'input': post_content[:50] + "..." if len(post_content) > 50 else post_content,
                            'output': like_action,
                            'timestamp': datetime.now()
                        })
                        
                except Exception as e:
                    st.error(f"Error simulating like: {str(e)}")
            else:
                st.warning("Please enter post content first!")

def handle_agent_thoughts():
    """Handle agent thoughts display"""
    st.subheader("💭 Agent Thoughts")
    
    if st.button("🧠 Generate Thoughts", type="primary"):
        try:
            with st.spinner("Accessing agent thoughts..."):
                thoughts = st.session_state.agent.think()
                
                st.success("✅ Thoughts generated!")
                st.text_area("Agent Thoughts", value=thoughts, height=150, disabled=True)
                
                # Add to history
                st.session_state.interaction_history.append({
                    'type': 'Agent Thoughts',
                    'input': 'Internal reflection',
                    'output': thoughts,
                    'timestamp': datetime.now()
                })
                
        except Exception as e:
            st.error(f"Error generating thoughts: {str(e)}")

def sidebar():
    """Display sidebar with user info and controls"""
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.username}!")
        
        if st.button("🚪 Logout"):
            logout()
        
        st.markdown("---")
        
        if st.session_state.agent:
            st.markdown("### 🏎️ Current Agent")
            agent_info = st.session_state.agent.get_agent_info()
            st.write(f"**Driver:** {agent_info['racer_name']}")
            st.write(f"**Team:** {agent_info['team_name']}")
            st.write(f"**Stage:** {agent_info['current_stage'].title()}")
            st.write(f"**Mood:** {agent_info['mood'].title()}")
            
            if agent_info.get('last_result'):
                st.write(f"**Last Result:** {agent_info['last_result'].title()}")
            
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        F1 Racer AI Agent powered by:
        - 🤖 LangChain
        - 🧠 Azure OpenAI GPT-4o-mini
        - ⚡ Streamlit
        """)

def main():
    """Main application function"""
    initialize_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Display sidebar
    sidebar()
    
    # Main content area
    tab1, tab2 = st.tabs(["🏁 Context Config", "🏎️ Agent Interaction"])
    
    with tab1:
        context_config_tab()
    
    with tab2:
        agent_interaction_tab()

if __name__ == "__main__":
    main()
