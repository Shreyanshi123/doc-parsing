# AI agent

An **AI agent** is an artificial intelligence program that can make decisions, pursue goals, and take actions independently on human programmers.[1][2][3] Agentic AI contrasts with tool-like AI use for narrow, specific tasks such as answering questions - as with chatbots in the non-agentic forms that were common in 2023, or with traditional machine learning algorithms.

While there is no universally agreed-upon definition of an AI agent,[4][5][6][7] common attributes of AI agents include goal-directed behavior, use of external tools, the ability to interact with and modify an external environment, and the ability to autonomously perform multi-step tasks. Their control flow is frequently driven by large language models (LLMs).[8] Agent systems may also include memory components, planning logic, tool interfaces, and orchestration software for coordinating agent components.[2][9]

---

## History

The theoretical underpinnings for artificial agents emerged in the mid 20th century, with establishment of cybernetics and artificial intelligence. Oliver Selfridge's 1958 "Pandemonium: A Paradigm for Learning" paper was an important early theoretical contribution in establishing agent oriented architecture. Practical implementations of agents for real world applications began to become widespread in the 1990s, after the introduction of the belief–desire–intention software model (BDI), and agent-oriented programming. Harvard professor Milind Tambe notes that in the 1990s, the definition of an AI agent was not clear. Pure digital agents were deployed in computer infrastructure for purposes such as monitoring, while agents connected to real-world sensors and actuators were increasingly used in industrial control systems.[10][11][12]

Early artificial agents tended to have simple if then logic, which expanded over time into large decision tree models. By the early 2010s, products like Siri and Alexa were released, and were sometimes called AI agents, though they lacked the general purpose reasoning ability of later agents run by large language models (LLMs). The development of LLMs during the late 2010s and early 2020s introduced new approaches to AI agents. Models such as GPT-3 demonstrated the ability to generate and understand natural language at a much larger scale than many earlier language systems.[13]

Academics began to study LLM agents from 2018. Deployment of such agents began to accelerate in late 2023 after OpenAI's "function-calling" API was made available, and especially after Anthropic's late 2024 introduction of Model Context Protocol (MCP), a standardised way for LLM agents to gain contextual awareness, and to act on the world by calling various external tools. The term "agentic" only began to be used with any frequency in 2024, popularised in part by researcher Andrew Ng.[14][13]

# Training and testing

Researchers have attempted to build world models[15][16] and reinforcement learning environments[17] to train or evaluate AI agents. For example, video games such as Minecraft[18] and No Man's Sky[19] as well as replicas of company websites,[20] have also been used for training such agents.

# Autonomous capabilities

The *Financial Times* compared AI agents' autonomy to the SAE classification of self-driving cars, likening most applications to level 2 or level 3, with some achieving level 4 in highly specialized circumstances and level 5 being theoretical.[21]

# Cognitive architecture

Ken Huang proposed an AI agent reference architecture that consists of seven interconnected layers, with each layer building on the functionality of the layers beneath it:[22]

- **Layer 1: Foundation models** – provide the datasets that power the agent.
- **Layer 2: Data operations** – manages the data infrastructure required for AI agent operations, including vector databases, data loaders, and RAG.
- **Layer 3: Agent frameworks** – software that manages the AI agents.
- **Layer 4: Deployment and infrastructure** – the technical foundation of the AI agents.
- **Layer 5: Evaluation and observability** – the safety and performance of AI agents.
- **Layer 6: Security and compliance** – a protective framework for safe operation and compliance with regulatory boundaries. At this layer, security and compliance features embedded into all the AI agent stack layers are integrated together.
- **Layer 7: Agent ecosystem** – represents the AI agents' interface with real-world applications and users.

# Agent harness

An agent harness, or agent scaffold, is the software layer surrounding a large language model that enables it to function as an AI agent. It commonly manages prompts, context, tool use, memory, execution state, operational constraints, sandboxes, permissions, and the processing of results. The harness connects the model to internal and external computer hardware, software, data files, databases, web browsers, command-line interfaces, and application programming interfaces, while controlling how the agent accesses and uses these resources to complete multi-step tasks.[23][24]

# Agent orchestration

An agent orchestration is a layer surrounding multiple AI agents. The goal of agent orchestration is to produce a coherent group out of these AI agents, that is, a thing that achieves better results than a minimal "no orchestration" solution: running these agents in parallel without interaction, and synthesizing their

outputs.

Relatedly, a workflow is a layer surrounding an AI agent, or a group of AI agents, intended to allow better performance on certain tasks that has to progress in stages, or tight integration with specialized tasks.

Examples include the following:[25]

- **Prompt chaining:** A sequence where the output of one step serves as the input for the next.
- **Routing:** Directing an input to a specialized downstream task or tool.
- **Parallelization:** The simultaneous execution of multiple tasks.
- **Sequential processing:** A fixed, linear progression of tasks through a predefined pipeline.
- **Planner-critic:** An iterative pattern where one agent generates a proposal and another evaluates it to provide feedback for refinement.

# Multimodal AI agents

In addition to large language models (LLMs), vision-language models (VLMs) and multimodal foundation models can be used as the basis for agents. Allen Institute for AI released an open-source vision-language model in 2024.[26] Nvidia released a framework for developers to use VLMs, LLMs and retrieval-augmented generation for building AI agents that can analyze images and videos, including video search and video summarization.[27][28] Microsoft released a multimodal agent model – trained on images, video, software user interface interactions, and robotics data – that the company claimed can manipulate software and robots.[29]

# Applications

*The Information* divided AI agents into seven archetypes: business-task agents, for acting within enterprise software; conversational agents, which act as chatbots for customer support; research agents, for querying and analyzing information (such as OpenAI Deep Research); analytics agents, for analyzing data to create reports; software developer or coding agents (such as Cursor); domain-specific agents, which include specific subject matter knowledge; and web browser agents (such as OpenAI Operator).[30]

By mid-2025, AI agents were being used in video game development,[31] gambling (including sports betting),[32] cryptocurrency wallets[32] (including cryptocurrency trading and meme coins[33]) and social media.[34] In August 2025, *New York Magazine* described software development as the most definitive use of AI agents.[35] *The Information* noted AI coding agents and customer support as the primary uses of AI by businesses by October 2025, although a decline in the expectations of AI capabilities was also noted.[36]

In November 2025, *The Wall Street Journal* reported that few companies that deployed AI agents have received a return on investment.[37]

## Government

Several government bodies in the United States and United Kingdom have deployed or announced the deployment of agents at the local and national level. The city of Kyle, Texas deployed an AI agent from Salesforce in March 2025 for 311 customer service.[38] In November 2025, the Internal Revenue Service