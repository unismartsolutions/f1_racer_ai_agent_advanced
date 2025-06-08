# Submission F1 Racer AI Agent - Advanced
## Created by Tevin Richard

## Overview 
This is a more advanced attempt at creating the requested  Formula 1 racer simulation system that generates authentic social media content and fan interactions using advanced Natural Language Processing capabilities. The agent was designed and developed to utilise an OpenAI GPT-4o-mini model for creating authentic and human-like responses. This solution leverages the Agentic AI Framework - Langchain which utilizes the power of LLMs to create agentic applications.

## Key Notes: 

1. The same assessment rules were followed when developing this solution, howver this implementation offers the following benefits:

  - Enhanced response generation using GPT-4o-mini model
  - Clean Streamlit user interface
  - Web app deployment (Docker image via Github actions and served through Azure Web Application)


## File Structure

  - streamlit_app.py: Main web application interface
  - f1_agent_langchain.py: Core AI agent implementation using LangChain
  - auth.py: User authentication system
  - config.py: Application configuration management
  - Dockerfile: Container configuration for deployment
  - deploy.yml: CI/CD pipeline for Azure deployment

## Usage
1. Log in with provided credentials
2. Configure the agent with driver name, team, race context, and mood
3. Choose interaction types from the available options:
  - Generate status posts
  - Reply to fan comments
  - Create mentions of other drivers
  - Simulate social media reactions
  - View agent's internal thoughts
  - View interaction history to track generated content

Technical Details
  - Developed using Streamlit for a seamless web interface.
  - Integrates LangChain and Azure OpenAI for advanced AI features.
  - Packaged with Docker for efficient deployment.
  - Automated deployment via GitHub Actions to Azure Web App.
  - Features a dark-themed UI inspired by racing aesthetics.


## Running Locally
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```
