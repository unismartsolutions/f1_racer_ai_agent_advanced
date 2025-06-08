import random
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

# LangChain imports
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import LLMChain

# Configuration
from config import get_config

class RaceStage(Enum):
    """Represents the main stages of a Formula 1 race weekend."""
    PRACTICE = "practice"
    QUALIFYING = "qualifying"
    RACE = "race"
    POST_RACE = "post_race"

class SessionType(Enum):
    """Enumerates the specific session types during a race weekend."""
    FP1 = "FP1"
    FP2 = "FP2"
    FP3 = "FP3"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    RACE = "Race"

class RaceResult(Enum):
    """Possible outcomes or results for a driver in a race."""
    WIN = "win"
    PODIUM = "podium"
    POINTS = "points"
    DNF = "dnf"
    CRASH = "crash"
    MECHANICAL = "mechanical"
    DISAPPOINTING = "disappointing"

@dataclass
class RaceContext:
    """Race weekend context data"""
    stage: RaceStage
    session_type: Optional[SessionType]
    circuit_name: str
    race_name: str
    last_result: Optional[RaceResult]
    position: Optional[int]
    team_name: str
    racer_name: str
    mood: str

class LangChainProcessor:
    """LangChain processor using Azure OpenAI"""
    
    def __init__(self):
        self.config = get_config()
        self.llm = self._initialize_llm()
        self._initialize_chains()
    
    def _initialize_llm(self):
        """Initialize Azure OpenAI LLM"""
        return AzureChatOpenAI(
            azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT,
            api_key=self.config.AZURE_OPENAI_API_KEY,
            api_version=self.config.AZURE_OPENAI_API_VERSION,
            deployment_name=self.config.AZURE_OPENAI_DEPLOYMENT_NAME,
            temperature=0.7,
            max_tokens=500
        )
    
    def _initialize_chains(self):
        """Initialize LangChain chains for different tasks"""
        
        # Sentiment analysis chain
        sentiment_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at analyzing sentiment in social media comments. Analyze the sentiment and return a score between -1 (very negative) and 1 (very positive), plus a brief explanation."),
            ("human", "Analyze this comment: '{comment}'\n\nReturn format: Score: X.X, Explanation: brief explanation")
        ])
        
        self.sentiment_chain = sentiment_prompt | self.llm | StrOutputParser()
        
        # Content generation chain
        content_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are {racer_name}, a professional Formula 1 driver for {team_name}. 
            Your current context:
            - Race Stage: {stage}
            - Session: {session_type}
            - Circuit: {circuit_name}
            - Race: {race_name}
            - Recent Result: {last_result}
            - Position: {position}
            - Current Mood: {mood}
            
            Generate authentic F1 social media content that matches your personality and current situation.
            Keep it engaging, use appropriate F1 terminology, and include relevant hashtags.
            Be authentic to the emotional state based on recent results."""),
            ("human", "Generate a {content_type} social media post.")
        ])
        
        self.content_chain = content_prompt | self.llm | StrOutputParser()
        
        # Reply generation chain
        reply_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are {racer_name}, a professional Formula 1 driver for {team_name}.
            Your current context:
            - Race Stage: {stage}
            - Circuit: {circuit_name}
            - Recent Result: {last_result}
            - Current Mood: {mood}
            
            Respond to fan comments professionally and authentically. Match the tone of the original comment.
            Be engaging, appreciative of fans, and maintain your professional image.
            Keep responses concise but meaningful."""),
            ("human", "Respond to this fan comment: '{fan_comment}'")
        ])
        
        self.reply_chain = reply_prompt | self.llm | StrOutputParser()
        
        # Mention generation chain
        mention_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are {racer_name}, a professional Formula 1 driver for {team_name}.
            Generate a social media mention about another person in F1.
            Context: {mention_context}
            
            Keep it professional, respectful, and authentic to F1 culture.
            Include appropriate hashtags and maintain competitive spirit."""),
            ("human", "Create a {mention_context} mention about @{person_name}")
        ])
        
        self.mention_chain = mention_prompt | self.llm | StrOutputParser()
        
        # Thoughts generation chain
        thoughts_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are {racer_name}, a professional Formula 1 driver.
            Your current context:
            - Race Stage: {stage}
            - Session: {session_type}
            - Circuit: {circuit_name}
            - Recent Result: {last_result}
            - Current Mood: {mood}
            
            Generate internal thoughts that reflect your mental state and focus.
            Be introspective, strategic, and authentic to a professional racing driver's mindset."""),
            ("human", "What are your current internal thoughts and focus?")
        ])
        
        self.thoughts_chain = thoughts_prompt | self.llm | StrOutputParser()
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using LangChain and Azure OpenAI"""
        try:
            result = self.sentiment_chain.invoke({"comment": text})
            
            # Parse the result to extract score
            score_line = [line for line in result.split('\n') if 'Score:' in line]
            if score_line:
                score_str = score_line[0].split('Score:')[1].split(',')[0].strip()
                compound = float(score_str)
            else:
                compound = 0.0
            
            # Convert compound score to individual scores
            if compound > 0.1:
                pos = min(1.0, compound + 0.3)
                neg = max(0.0, 0.1 - compound)
            elif compound < -0.1:
                pos = max(0.0, 0.1 + compound)
                neg = min(1.0, abs(compound) + 0.3)
            else:
                pos = 0.5
                neg = 0.5
            
            neu = max(0.0, 1.0 - pos - neg)
            
            return {
                'compound': max(-1.0, min(1.0, compound)),
                'pos': pos,
                'neg': neg,
                'neu': neu
            }
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return {'compound': 0.0, 'pos': 0.5, 'neg': 0.5, 'neu': 0.0}
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using simple text processing"""
        import re
        
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return list(set(keywords))

class F1RacerAgent:
    """
    F1 Racer AI Agent powered by LangChain and Azure OpenAI
    """
    
    def __init__(self, racer_name: str = "Lightning McQueen", team_name: str = "Rusteze Racing"):
        self.racer_name = racer_name
        self.team_name = team_name
        self.context = RaceContext(
            stage=RaceStage.PRACTICE,
            session_type=SessionType.FP1,
            circuit_name="Circuit",
            race_name="Grand Prix",
            last_result=None,
            position=None,
            team_name=team_name,
            racer_name=racer_name,
            mood="focused"
        )
        
        try:
            self.processor = LangChainProcessor()
            self.processor_ready = True
        except Exception as e:
            print(f"Warning: LangChain processor failed to initialize: {e}")
            self.processor_ready = False
        
        self.recent_posts = []
        self.interaction_history = []
        self.max_recent_posts = 10
        
        # Initialize fallback response library
        self._init_fallback_responses()
    
    def _init_fallback_responses(self):
        """Initialize fallback responses for when LangChain is unavailable"""
        self.fallback_responses = {
            "win": [
                "YES! What an incredible race! Can't believe we pulled that off! 🏆 #Victory #F1",
                "VICTORY! Absolutely buzzing right now! Massive thanks to the entire team! 🥇 #ChampionMindset",
                "P1! What a feeling! The car was absolutely perfect today! 🏁 #Winner"
            ],
            "podium": [
                "Great result today! Really happy with the progress we're making! 🏆 #Podium #TeamWork",
                "P3! Solid points in the bag! Team did an amazing job! 💪 #Points",
                "Happy with that result! We maximized what we had today! 🏁 #F1"
            ],
            "disappointing": [
                "Tough day but these things happen in racing. We'll bounce back stronger! 💪 #NeverGiveUp",
                "Not our day today but the team never gives up. On to the next one! 🏁 #TeamSpirit",
                "Disappointed but that's racing. Already looking ahead to next weekend! 🔄 #ComeBackStronger"
            ],
            "practice": [
                "Good session today! Learning more about the car with every lap! 🏎️ #FP2 #Progress",
                "Productive practice session! Getting the setup dialed in nicely! 🔧 #TeamWork",
                "Solid work in practice today! The car is feeling better and better! 📈 #F1"
            ],
            "qualifying": [
                "Qualifying day! Time to find those extra tenths! Car feels good! ⏱️ #Quali #Speed",
                "Ready for quali! The setup feels solid! Let's see what we can do! 🏁 #QualifyingMode",
                "Q-day! Feeling confident about our pace! Time to put it together! 💨 #F1"
            ],
            "general": [
                "Always giving 100% for the team and the fans! 🏎️ #F1 #TeamWork",
                "Another day at the office! Love what I do! ❤️ #LivingTheDream #Racing",
                "Working hard with the team to extract every bit of performance! 🔧 #F1"
            ]
        }
    
    def update_context(self, stage: RaceStage, session_type: Optional[SessionType] = None,
                      circuit_name: str = None, race_name: str = None,
                      last_result: Optional[RaceResult] = None, position: Optional[int] = None,
                      mood: str = None):
        """Update the agent's contextual awareness"""
        
        if circuit_name:
            self.context.circuit_name = circuit_name
        if race_name:
            self.context.race_name = race_name
        
        self.context.stage = stage
        self.context.session_type = session_type
        self.context.last_result = last_result
        self.context.position = position
        
        if mood:
            self.context.mood = mood
        else:
            self._analyze_and_update_mood()
        
        context_change = {
            "timestamp": datetime.now(),
            "stage": stage.value,
            "mood": self.context.mood
        }
        self.interaction_history.append(context_change)
    
    def _analyze_and_update_mood(self):
        """Analyze and update mood based on context"""
        if self.context.last_result:
            if self.context.last_result == RaceResult.WIN:
                self.context.mood = "ecstatic"
            elif self.context.last_result in [RaceResult.PODIUM, RaceResult.POINTS]:
                self.context.mood = "positive"
            elif self.context.last_result in [RaceResult.DNF, RaceResult.CRASH, RaceResult.DISAPPOINTING]:
                self.context.mood = "disappointed"
            else:
                self.context.mood = "neutral"
        else:
            if self.context.stage == RaceStage.PRACTICE:
                self.context.mood = "focused"
            elif self.context.stage == RaceStage.QUALIFYING:
                self.context.mood = "intense"
            elif self.context.stage == RaceStage.RACE:
                self.context.mood = "determined"
            else:
                self.context.mood = "neutral"
    
    def speak(self, context_type: str = "general") -> str:
        """Generate contextual F1 racer posts using LangChain"""
        
        if not self.processor_ready:
            return self._fallback_speak(context_type)
        
        try:
            # Prepare context for LangChain
            context_vars = {
                "racer_name": self.racer_name,
                "team_name": self.team_name,
                "stage": self.context.stage.value,
                "session_type": self.context.session_type.value if self.context.session_type else "N/A",
                "circuit_name": self.context.circuit_name,
                "race_name": self.context.race_name,
                "last_result": self.context.last_result.value if self.context.last_result else "N/A",
                "position": str(self.context.position) if self.context.position else "N/A",
                "mood": self.context.mood,
                "content_type": context_type
            }
            
            # Generate content using LangChain
            content = self.processor.content_chain.invoke(context_vars)
            
            # Clean up the response
            content = content.strip()
            if not content:
                return self._fallback_speak(context_type)
            
            # Track the post
            self._track_generated_content(content, context_type)
            
            return content
            
        except Exception as e:
            print(f"LangChain content generation error: {e}")
            return self._fallback_speak(context_type)
    
    def _fallback_speak(self, context_type: str) -> str:
        """Fallback content generation when LangChain is unavailable"""
        
        # Map context type to available responses
        if context_type == "general":
            context_type = self._determine_context_from_state()
        
        if context_type in self.fallback_responses:
            base_messages = self.fallback_responses[context_type]
            message = random.choice(base_messages)
        else:
            message = random.choice(self.fallback_responses["general"])
        
        # Add circuit/race context
        if self.context.race_name and "Grand Prix" in self.context.race_name:
            race_hashtag = self.context.race_name.replace(" Grand Prix", "GP").replace(" ", "")
            message += f" #{race_hashtag}"
        
        return message
    
    def _determine_context_from_state(self) -> str:
        """Determine context type from current agent state"""
        if self.context.last_result == RaceResult.WIN:
            return "win"
        elif self.context.last_result == RaceResult.PODIUM:
            return "podium"
        elif self.context.last_result in [RaceResult.DNF, RaceResult.CRASH, RaceResult.DISAPPOINTING]:
            return "disappointing"
        elif self.context.stage == RaceStage.PRACTICE:
            return "practice"
        elif self.context.stage == RaceStage.QUALIFYING:
            return "qualifying"
        else:
            return "general"
    
    def reply_to_comment(self, original_comment: str) -> str:
        """Generate contextual reply to fan comments using LangChain"""
        
        if not self.processor_ready:
            return self._fallback_reply(original_comment)
        
        try:
            # Prepare context for LangChain
            context_vars = {
                "racer_name": self.racer_name,
                "team_name": self.team_name,
                "stage": self.context.stage.value,
                "circuit_name": self.context.circuit_name,
                "last_result": self.context.last_result.value if self.context.last_result else "N/A",
                "mood": self.context.mood,
                "fan_comment": original_comment
            }
            
            # Generate reply using LangChain
            reply = self.processor.reply_chain.invoke(context_vars)
            
            # Clean up the response
            reply = reply.strip()
            if not reply:
                return self._fallback_reply(original_comment)
            
            return reply
            
        except Exception as e:
            print(f"LangChain reply generation error: {e}")
            return self._fallback_reply(original_comment)
    
    def _fallback_reply(self, original_comment: str) -> str:
        """Fallback reply generation"""
        
        comment_lower = original_comment.lower()
        
        # Simple sentiment analysis
        positive_words = ['amazing', 'great', 'awesome', 'fantastic', 'brilliant', 'excellent']
        negative_words = ['bad', 'terrible', 'awful', 'disappointing', 'frustrating']
        question_words = ['what', 'how', 'why', 'when', 'where', 'which', 'who']
        
        if any(word in comment_lower for word in positive_words):
            replies = [
                "Thank you! Your support means everything! 🙏❤️",
                "Really appreciate it! Messages like this keep us motivated! 😊🏁",
                "Thanks! The fans are what make this sport so special! 🏎️💙"
            ]
        elif any(word in comment_lower for word in negative_words):
            replies = [
                "Thanks for the honest feedback! We'll use it to get better! 💪🙏",
                "Appreciate the perspective! Every opinion helps us improve! 👍",
                "Fair point! We're always working to do better! 🔧💙"
            ]
        elif any(word in comment_lower for word in question_words) or '?' in comment_lower:
            replies = [
                "Great question! Always happy to connect with curious fans! 🤔😊",
                "Thanks for asking! Love the engagement from supporters! 🙏💭",
                "Good question! The fans ask the most interesting things! 😊🏁"
            ]
        else:
            replies = [
                "Thanks for the comment! Love connecting with fans! 🙏😊",
                "Appreciate the message! Fan support is incredible! ❤️🏁",
                "Thanks! Great to hear from the racing community! 👍🏎️"
            ]
        
        return random.choice(replies)
    
    def mention_teammate_or_competitor(self, person_name: str, context: str = "positive") -> str:
        """Generate mention posts using LangChain"""
        
        if not self.processor_ready:
            return self._fallback_mention(person_name, context)
        
        try:
            # Prepare context for LangChain
            context_vars = {
                "racer_name": self.racer_name,
                "team_name": self.team_name,
                "mention_context": context,
                "person_name": person_name
            }
            
            # Generate mention using LangChain
            mention = self.processor.mention_chain.invoke(context_vars)
            
            # Clean up the response
            mention = mention.strip()
            if not mention:
                return self._fallback_mention(person_name, context)
            
            return mention
            
        except Exception as e:
            print(f"LangChain mention generation error: {e}")
            return self._fallback_mention(person_name, context)
    
    def _fallback_mention(self, person_name: str, context: str) -> str:
        """Fallback mention generation"""
        
        mention_templates = {
            "positive": [
                f"Great work by @{person_name}! Love the level of competition in F1! 🏁 #Respect #F1",
                f"Respect to @{person_name} for that performance! This is what racing is all about! 🏎️ #Racing",
                f"Hat off to @{person_name}! Amazing driving today! 👏 #F1 #Competition"
            ],
            "teammate": [
                f"Team effort with @{person_name} today! Great to have such a strong teammate! 💪 #{self.team_name.replace(' ', '')}",
                f"Solid work @{person_name}! Together we make {self.team_name} stronger! 🏁 #TeamWork",
                f"@{person_name} bringing the speed! Teamwork makes the dream work! ⚡ #F1"
            ],
            "competitive": [
                f"Ready for the battle with @{person_name}! Should be great racing tomorrow! 🏁 #Competition",
                f"Looking forward to racing @{person_name}! Competition at its finest! 🏎️ #F1",
                f"@{person_name} bringing the heat! Love these battles! 🔥 #Racing"
            ]
        }
        
        templates = mention_templates.get(context, mention_templates["positive"])
        return random.choice(templates)
    
    def simulate_like_action(self, post_content: str) -> str:
        """Simulate liking a post with sentiment analysis"""
        
        try:
            if self.processor_ready:
                sentiment = self.processor.analyze_sentiment(post_content)
                compound = sentiment['compound']
            else:
                # Simple fallback sentiment
                positive_words = ['great', 'amazing', 'awesome', 'fantastic', 'excellent']
                negative_words = ['bad', 'terrible', 'awful', 'disappointing']
                
                post_lower = post_content.lower()
                pos_count = sum(1 for word in positive_words if word in post_lower)
                neg_count = sum(1 for word in negative_words if word in post_lower)
                compound = (pos_count - neg_count) / 5.0
            
            if compound > 0.5:
                reactions = ["❤️ Loved", "❤️❤️❤️ Absolutely loved", "💪 Fully supported", "🔥 This is fire"]
            elif compound > 0.1:
                reactions = ["👍 Liked", "🙌 Supported", "💯 This", "✨ Quality content"]
            else:
                reactions = ["👍 Acknowledged", "🤝 Respect", "💙 Seen", "👍 Noted"]
            
            action = random.choice(reactions)
            preview = post_content[:50] + "..." if len(post_content) > 50 else post_content
            
            return f"{action}: '{preview}'"
            
        except Exception as e:
            print(f"Like simulation error: {e}")
            return f"👍 Liked: '{post_content[:50]}...'"
    
    def think(self) -> str:
        """Generate internal thoughts using LangChain"""
        
        if not self.processor_ready:
            return self._fallback_think()
        
        try:
            # Prepare context for LangChain
            context_vars = {
                "racer_name": self.racer_name,
                "stage": self.context.stage.value,
                "session_type": self.context.session_type.value if self.context.session_type else "N/A",
                "circuit_name": self.context.circuit_name,
                "last_result": self.context.last_result.value if self.context.last_result else "N/A",
                "mood": self.context.mood
            }
            
            # Generate thoughts using LangChain
            thoughts = self.processor.thoughts_chain.invoke(context_vars)
            
            # Clean up the response
            thoughts = thoughts.strip()
            if not thoughts:
                return self._fallback_think()
            
            return f"💭 Internal thoughts: {thoughts}"
            
        except Exception as e:
            print(f"LangChain thoughts generation error: {e}")
            return self._fallback_think()
    
    def _fallback_think(self) -> str:
        """Fallback thoughts generation"""
        
        thoughts = []
        
        if self.context.stage == RaceStage.PRACTICE:
            thoughts.extend([
                f"Focusing on the setup for {self.context.circuit_name}.",
                "Every lap teaches us something new about the car.",
                "Working closely with the engineers to find the right balance."
            ])
        elif self.context.stage == RaceStage.QUALIFYING:
            thoughts.extend([
                "Every tenth counts in qualifying. Mental preparation is key.",
                "Need to find that perfect lap when it matters most.",
                "The car setup needs to be spot on for tomorrow."
            ])
        elif self.context.stage == RaceStage.RACE:
            thoughts.extend([
                "Race day is what we live for. Time to execute the plan.",
                "Managing tires and fuel will be crucial today.",
                "Stay calm, hit your marks, capitalize on opportunities."
            ])
        else:
            thoughts.extend([
                "Reflecting on the weekend and looking ahead.",
                "Always learning, always improving.",
                "The team's dedication never ceases to amaze me."
            ])
        
        selected_thoughts = random.sample(thoughts, min(2, len(thoughts)))
        return f"💭 Internal thoughts: {' '.join(selected_thoughts)}"
    
    def _track_generated_content(self, content: str, context_type: str):
        """Track generated content for analysis"""
        
        entry = {
            "timestamp": datetime.now(),
            "content": content,
            "context_type": context_type,
            "mood": self.context.mood,
            "stage": self.context.stage.value
        }
        
        self.recent_posts.append(entry)
        
        if len(self.recent_posts) > self.max_recent_posts:
            self.recent_posts.pop(0)
    
    def get_agent_info(self) -> Dict:
        """Return comprehensive agent state"""
        
        return {
            "racer_name": self.racer_name,
            "team_name": self.team_name,
            "current_stage": self.context.stage,
            "session_type": self.context.session_type,
            "circuit": self.context.circuit_name,
            "race": self.context.race_name,
            "last_result": self.context.last_result,
            "position": self.context.position,
            "mood": self.context.mood,
            "recent_posts_count": len(self.recent_posts),
            "interaction_history_count": len(self.interaction_history),
            "processor_ready": self.processor_ready
        }
