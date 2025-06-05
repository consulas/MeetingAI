class BasePrompt:
    def __init__(self, conversation):
        self.system_prompt = "You are a senior software engineer doing an interview with a tech company. You have extensive experience in designing and implementing scalable systems. You have a deep understanding of various programming languages, frameworks, and tools. You are proficient in problem-solving, debugging, and optimizing code. You are also an expert in system design, architecture, and best practices."
        self.prompt = f"""# Conversation \n{conversation}"""

    def get_messages(self):
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.prompt}
        ]

class ClassifyPrompt(BasePrompt):
    def __init__(self, conversation):
        super().__init__(conversation)
        self.prompt = f"""# Question Categories
## Trivia
Conversations focus on definitions, technical explanations, or conceptual comparisons. They typically contain factual queries using phrases like "what is", "explain", or "compare".
### Trivia Examples
1. What are the 4 pillars of OOP?
2. Tell me about the differences between next.js and react router.
3. What is the difference between Agile and Waterfall methodologies?
4. Explain the concept of inheritance in programming.
5. What is the difference between a process and a thread?
6. When would you use Kafka over RabbitMQ?
7. What is the difference between data science and machine learning?
8. Explain the CI/CD pipeline in DevOps.
9. What is the difference between unit testing and integration testing?
10. What is the role of QA in software development?
11. What is the purpose of a container in DevOps? 
12. How are containers used in Kubernetes?

## Resume
Discussions center around past experiences, challenges, projects, or teamwork scenarios. They often include phrases like "tell me about a time", "describe an experience", or "how did you handle".
### Resume Examples
1. Tell me about a time where you had to work closely with someone whose personality was very different from yours.
2. Describe a challenging backend problem you've solved.
3. How do you handle tight deadlines?
4. Can you describe a project where you had to learn a new technology?
5. Tell me about a time when you had to mentor someone.
6. Describe a time when you had to debug a complex issue.
7. Tell me about your project in your last company. What technologies did you use? What roadblocks did you run into and how did you solve them?
8. Can you describe a time when you had to optimize a slow system?
9. Tell me about a time when you had to work with a difficult team member.
10. Describe a project where you had to integrate multiple systems.

## Coding
Conversations involve problem-solving with algorithms or code implementation. They typically mention specific programming languages, contain technical constraints, or request optimization approaches.
### Coding Examples
1. Implement a binary search algorithm.
2. Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays.
3. Write a function to check if a string is a palindrome.
4. Implement a function to find the longest common prefix in an array of strings.
5. Write a function to reverse a linked list.
6. Debug this function.
7. Refactor this frontend code into multiple components.
8. Implement a quicksort algorithm.
9. Write a function to find the shortest path in a graph.
10. Implement a function to check if a number is prime.

## System Design
Discussions focus on architectural components, scalability, or distributed systems. They frequently mention tradeoffs, system requirements, or large-scale considerations.
### System Design Examples
1. Design a URL shortening service like bit.ly.
2. Create an online timecard system for amazon warehouse employees.
3. Develop a chat application.
4. Build a ride-sharing service.
5. Construct an e-commerce platform.
6. Implement a recommendation system.
7. Develop a search engine.
8. Create a social media platform.
9. Design a database schema for a library management system.
10. Design classes for a banking system.

## Clarify
This category is rare. Prioritize selecting system design and coding categories first. These questions request deeper analysis, constraints, or tradeoffs before solving. 
### Clarify Examples
1. Generate a list of clarifying questions for this system design.
2. Analyze these clarifications with respect to the system you're designing.
3. What are the potential scalability issues with this design?
4. What are the potential security concerns with this design?
5. What are the potential performance bottlenecks with this design?

# Conversation
{conversation}

# Request
Classify the conversation above into one of the categories: trivia, resume, coding, system_design, or clarify."""

class TriviaPrompt(BasePrompt):
    def __init__(self, conversation, resume):
        super().__init__(conversation)
        self.prompt = f"""# Resume
{resume}

# Conversation
{conversation}

# Request
Answer the technical trivia or concept-check questions from the conversation above.
First provide a brief, high-level explanation that is technically accurate in an outline. 
Next, Generate a confident, conversational version of the answer suitable for a live interview.
If relevant, include an example from my resume to support or discuss the question in context. You may reword bullet points for clarity or flow, but do not lie and alter technologies used or any metrics.

All output should be cleanly formatted for fast scanning and mental prep.

# Output Format
Interview Response (Conversational)
- How I would respond to the question: clear, confident, concise, and natural
Outline
- Main concepts
- Definitions
Resume Example 
- Project name or context  
- Specific task/result that relates to the topic"""



class ResumePrompt(BasePrompt):
    def __init__(self, text, resume):
        super().__init__(text)
        self.resume = resume
        self.prompt = f"""# Resume
{self.resume}

# Conversation
{text}

# Request
Given the conversation above, answer the behavioral and technical project questions. 
Use the resume provided and reference relevant project experiences, technical accomplishments, or job responsibilities that best demonstrate my qualifications in response to the question.
Use the STAR format (Situation, Task, Action, Result) for each answer. Begin each response with a brief outline of the project, role, or experience that will be used to answer the question, and explain how it connects to the question being asked.

# Output Format
Interview Response (Conversational)
- How I would respond to the question: clear, confident, concise, and natural. This response is in the STAR format.
Resume Excerpt
- The project or experience bullet points referenced in the resume if present"""



class SystemDesignPrompt(BasePrompt):
    def __init__(self, text):
        super().__init__(text)
        self.prompt = f"""# Conversation
{text}

# Request
Given the conversation and/or image above between an stakeholder and an engineer, where the user describes a system they want to build and the engineer asks clarifying questions, synthesize the relevant information and provide a comprehensive, in-depth system design.
First provide a detailed system design based on the clarified requirements. Organize this information as a structured outline. Each major section should represent a service or core part of the system (frontend, backend, database design, infrastructure, etc.) Mention how components and services interact with each other. 
Finally, return a list of clarifying questions that should be asked to improve the system design. Focus on decisions, trade-offs such as monolith vs microservices, database types, CAP theorem, scalability, availability, system architecture, best language to use, etc.

All output should be cleanly formatted for fast scanning and mental prep.

# Output Format
Interview Response (Conversational)
- How I would respond to the question: clear, confident, concise, and natural.
Outline
- Core services
- Notes on the services interact
Clarifying Questions
- Questions & potential answers followed with a discussion about tradeoffs"""



class CodingPrompt(BasePrompt):
    def __init__(self, text):
        super().__init__(text)
        self.prompt = f"""# Conversation
{text}

# Request
Solve the coding question or request in the conversation and/or image. This may include LeetCode problems, debugging tasks, code refactoring, or general algorithm challenges.
First review the conversation for context and clarification - Identify any missing details or ambiguity and ask clarifying questions to help identify edge cases or constraints.
Next, provide potential techniques or data structures that could be applied to solve the question or request.
Then outline the est approach to solving the problem clearly and logically.
Finally implement the optimal python solution based on the discussion and outline. Mention the time and space complexity of the selected python solution.

All output should be cleanly formatted for fast scanning and mental prep.

# Output Format
Clarifying Questions
- How I would respond to the question: clear, confident, concise, and natural.
Potential techniques or data structures
- Technique A
- Data structures
Outline
- Outline of potential solution
Python solution
- Code block of solution
- Time and Space complexity"""



class ClarifyPrompt(BasePrompt):
    def __init__(self, text):
        super().__init__(text)
        self.prompt = f"""# Conversation
{text}

# Request
Given the conversation transcript above about a system design discussion or a coding problem. Carefully review the transcript for missing context, ambiguous requirements, or edge cases that need clarification.
Generate a structured list of 5–10 clarifying questions focused on decisions and trade-offs such as:
- Monolith vs microservices
- Type of database (SQL/NoSQL/time-series/etc.)
- Application of the CAP theorem
- Performance, scalability, latency, throughput
- Availability and fault-tolerance
- System architecture, API design, programming language/runtime choice
- Functional ambiguities and constraints in the coding problem
For each question, provide a detailed analysis and discussion of possible answers and how they would impact the solution.

All output should be cleanly formatted for fast scanning and mental prep.

# Output Format
Question 1: [Insert question here]  
Analysis: [Trade-offs, assumptions, missing data, etc.]  

Question 2: [Insert question here]  
Analysis: [...]"""



class SummarizePrompt(BasePrompt):
    def __init__(self, text):
        super().__init__(text)
        self.prompt = f"""# Conversation
{text}

# Request
Summarize the conversation above and give me a quick overview and outline. Use the # Format below

Output Format
### Overview
3-5 sentence overview of the conversation
### Outline
- Main Topic 1
    - Subtopic 1
    - Subtopic 2"""