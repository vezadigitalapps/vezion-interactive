# Veza Digital AI Agent - Stakeholder Guide

## 🤖 What is the Veza Digital AI Agent?

The Veza Digital AI Agent is an intelligent Slack bot that provides C-level executives and leadership teams with strategic insights about client projects, task management, and resource allocation. It connects to your ClickUp workspace and client database to deliver executive-level reports and analysis.

## 🎯 Available Tools & Capabilities

### **Client Management Tools**
1. **Client Discovery by Channel** - Automatically identifies which client you're discussing based on the Slack channel
2. **Client Search** - Find any client by name, even with partial matches
3. **Client Mapping** - Access complete client information including ClickUp IDs and Slack channels
4. **Cross-Channel Queries** - Ask about any client from any Slack channel

### **ClickUp Integration Tools**
1. **Task Retrieval** - Get tasks from specific client projects with filtering options
2. **Recent Activity** - See what's been updated in the last day/week/month
3. **Task Creation** - Create new tasks directly from Slack conversations
4. **Task Updates** - Modify existing tasks (status, priority, assignees, etc.)
5. **Task Details** - Get comprehensive information about specific tasks
6. **List Management** - Access list information and available statuses

### **Time Tracking & Analytics**
1. **Time Tracking** - Analyze hours spent on client projects
2. **Resource Allocation** - Understand team time distribution
3. **Project Profitability** - Insights into project efficiency and costs

## 💬 Types of Questions That Work

### **Project Status Inquiries**
- `@bot what's the latest with Webconnex?`
- `@bot what is the latest with this client` _(when in a client channel)_
- `@bot show me recent activity for Clarity`
- `@bot what's been happening with Dialectica this week?`
- `@bot give me a status update on Strivacity`

### **Task Management**
- `@bot create a task to follow up with Client X next week`
- `@bot add a task "Review proposal" for Webconnex`
- `@bot what tasks are assigned to John?`
- `@bot show me all open tasks for this client`
- `@bot update the status of task ABC123 to completed`

### **Time & Resource Analysis**
- `@bot how many hours have we spent on Webconnex this month?`
- `@bot what's our time allocation across all clients?`
- `@bot show me time tracking for September 2025`
- `@bot analyze resource utilization for this project`

### **Strategic Insights**
- `@bot what are the risks with the Clarity project?`
- `@bot give me an executive summary of client work this week`
- `@bot what opportunities do you see with our current projects?`
- `@bot analyze project health across our portfolio`

### **Cross-Channel Queries**
- `@bot what's happening with Clarity?` _(asked from any channel)_
- `@bot create a task for Dialectica` _(from any channel)_
- `@bot show me all client updates from this week` _(from any channel)_

## 🧵 Thread Conversations

### **How Threads Work**
1. **Initial Query**: Mention `@bot` with your question
2. **Thread Response**: Bot replies in a thread with loading indicator
3. **Follow-up Questions**: Continue the conversation without mentioning the bot
4. **Context Memory**: Bot remembers the entire conversation in each thread

### **Thread Examples**
```
You: @bot what's the latest on Webconnex?
Bot: [Detailed executive report about Webconnex]

You: what about their budget status?
Bot: [Budget analysis for Webconnex - knows context]

You: create a task for them
Bot: [Creates task for Webconnex - no need to specify client again]
```

## 📊 Response Format

### **Executive-Level Insights**
The bot provides strategic analysis, not just raw data:
- **Business Impact**: What does this data mean for the business?
- **Risk Assessment**: Potential issues and mitigation strategies
- **Opportunities**: Growth and optimization recommendations
- **Trends**: Patterns and insights from project data
- **Actionable Intelligence**: Next steps and recommendations

### **Slack Formatting**
All responses use proper Slack formatting:
- *Bold text* for emphasis
- _Italic text_ for definitions
- `Code snippets` for technical terms
- • Bullet points for lists
- 📊 Strategic use of emojis

## 🔧 Technical Capabilities

### **13 Available MCP Tools**
1. `get_client_mapping` - Find client by name
2. `search_client_mappings` - Fuzzy search across all client data
3. `get_client_by_channel_id` - Find client by Slack channel
4. `get_all_client_names` - List all available clients
5. `get_tasks_by_list_id` - Retrieve tasks with filtering
6. `get_tasks_updated_since` - Recent activity analysis
7. `create_task` - Create new ClickUp tasks
8. `update_task` - Modify existing tasks
9. `get_task_details` - Comprehensive task information
10. `get_list_details` - ClickUp list information
11. `get_time_tracking` - Time and resource analysis
12. `update_client_mapping` - Modify client information
13. `create_client_mapping` - Add new clients

### **Smart Context Awareness**
- **Current Date**: Knows today is September 5, 2025
- **Channel Context**: Understands which client channel you're in
- **Thread Memory**: Remembers conversation history
- **Cross-Reference**: Can discuss any client from any channel

## 🚀 Getting Started

### **Basic Usage**
1. **Mention the bot**: `@bot` followed by your question
2. **Wait for response**: Bot shows loading indicator while processing
3. **Continue conversation**: Ask follow-up questions in the thread
4. **Get insights**: Receive executive-level analysis and recommendations

### **Best Practices**
- Be specific about time ranges: "this week", "this month", "September 2025"
- Use client names when asking cross-channel questions
- Ask for insights, not just data: "what does this mean for the business?"
- Follow up with strategic questions: "what are the risks?", "what opportunities do you see?"

## 💡 Value Proposition

### **For C-Level Executives**
- **Strategic Oversight**: Real-time insights into all client projects
- **Risk Management**: Early identification of project issues
- **Resource Optimization**: Understanding of team allocation and efficiency
- **Business Intelligence**: Data-driven decision making support

### **For Project Managers**
- **Quick Status Updates**: Instant project summaries
- **Task Management**: Create and update tasks via natural language
- **Team Coordination**: Understand task assignments and progress
- **Time Tracking**: Monitor project hours and deadlines

### **For Leadership Teams**
- **Portfolio View**: Overview of all client work
- **Performance Metrics**: Time, budget, and delivery insights
- **Trend Analysis**: Patterns across projects and clients
- **Actionable Recommendations**: Next steps and strategic guidance

## 📞 Support & Questions

The Veza Digital AI Agent is designed to be intuitive and conversational. Simply ask questions naturally, and the bot will provide intelligent, executive-level responses with strategic insights and actionable recommendations.

**Ready to transform your project management with AI-powered insights!**
