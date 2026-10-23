# **AI agent**

An **AI agent** is an artificial intelligence program that can make decisions, pursue goals, and take actions <u>independently on human programmers.[1][2][3]</u> Agentic AI contrasts with tool-like AI use for narrow, specific tasks such as answering questions - as with chatbots in the non-agentic forms that were common in 2023, or with traditional machine learning algorithms.

While there is no universally agreed-upon definition of an AI agent ~~,~~ <u>[4][5][6][7] common attributes of AI</u> agents include goal-directed behavior, use of external tools, the ability to interact with and modify an external environment, and the ability to autonomously perform multi-step tasks. Their control flow is frequently driven by <u>large language models (LLMs)</u> ~~.~~ <u>[8] Agent systems may also include memory</u> components, planning logic, tool interfaces, and <u>orchestration software for coordinating agent [2][9]</u> components ~~.~~

### **History**

The theoretical underpinnings for artificial agents emerged in the mid 20th century, with establishment of <u>cybernetics and artificial intelligence. Oliver Selfridge's 1958 "Pandemonium: A Paradigm for Learning"</u> paper was an important early theoretical contribution in establishing agent oriented architecture. Practical implementations of agents for real world applications began to become widespread in the 1990s, after the introduction of the <u>belief–desire–intention software model (BDI), and agent-oriented programming.</u> Harvard professor Milind Tambe notes that in the 1990s, the definition of an AI agent was not clear. Pure digital agents were deployed in computer infrastructure for purposes such as monitoring, while agents connected to real-world <u>sensors and actuators were increasingly used in industrial control [10][11][12] systems.</u>

Early artificial agents tended to have simple if then logic, which expanded over time into large decision <u>tree models. By the early 2010s, products like Siri and Alexa were released, and were sometimes called</u> AI agents, though they lacked the general purpose reasoning ability of later agents run by large language models (LLMs). The development of LLMs during the late 2010s and early 2020s introduced new approaches to AI agents. Models such as <u>GPT-3 demonstrated the ability to generate and understand [13]</u> natural language at a much larger scale than many earlier language systems.

Academics began to study LLM agents from 2018. Deployment of such agents began to accelerate in late 2023 after OpenAI's "function-calling" API was made available, and especially after <u>Anthropic's late</u> 2024 introduction of <u>Model Context Protocol</u> (MCP), a standardised way for LLM agents to gain contextual awareness, and to act on the world by calling various external tools. The term "agentic" only began to be used with any frequency in 2024, popularised in part by researcher <u>Andrew Ng.[14][13]</u>

## Training and testing

Researchers have attempted to build world models[15][16]and reinforcement learning environments[17] to train or evaluate AI agents. For example, video games such as Minecraft[18]and No Man's Sky[19]as well as replicas of company websites,[20]have also been used for training such agents.

### Autonomous capabilities

The Financial Times compared AI agents' autonomy to the SAE classification of self-driving cars, likening most applications to level 2 or level 3, with some achieving level 4 in highly specialized circumstances and level 5 being theoretical.[21]

#### Cognitive architecture

Ken Huang proposed an AI agent reference architecture that consists of seven interconnected layers, with each layer building on the functionality of the layers beneath it:[22]

Ly n - o nt nt ma ne ns n ons including vector databases, data loaders, and RAG.

Layer 3: Agent frameworks – software that manages the Al agents. ■Layer 4: Deployment and infrastructure – the technical foundation of the Al agents. Layer 5: Evaluation and observability – the safety and performance of Al agents. ■Layer 6: Security and compliance – a protective framework for safe operation and compliance with regulatory boundaries. At this layer, security and compliance features eam s s he s her

Layer 7: Agent ecosystem – represents the Al agents' interface with real-world applications and users.

### Agent harness

An agent harness, or agent scaffold, is the software layer surrounding a large language model that enables it to function as an AI agent. It commonly manages prompts, context, tool use, memory, execution state, operational constraints, sandboxes, permissions, and the processing of results. The harness connects the model to internal and external computer hardware, software, data files, databases, web browsers, command-line interfaces, and application programming interfaces, while controllinghow the agent accesses and uses these resources to complete multi-step tasks.[23][24]

#### Agent orchestration

An agent orchestration is a layer surrounding multiple AI agents. The goal of agent orchestration is to produce a coherent group out of these AI agents, that is, a thing that achieves better results than a minimal "no orchestration" solution: running these agents in parallel without interaction, and synthesizing their

outputs.

Relatedly, a workflow is a layer surrounding an AI agent, or a group of AI agents, intended to allow better performance on certain tasks that has to progress in stages, or tight integration with specialized tasks.

Examples include the following ~~:~~ <u>[25]</u>

- Prompt chaining: A sequence where the output of one step serves as the input for the next. Routing: Directing an input to a specialized downstream task or tool.

- Parallelization: The simultaneous execution of multiple tasks.

- Sequential processing: A fixed, linear progression of tasks through a predefined pipeline. Planner-critic: An iterative pattern where one agent generates a proposal and another evaluates it to provide feedback for refinement.

### **Multimodal AI agents**

In addition to large language models (LLMs), <u>vision-language models</u> (VLMs) and <u>multimodal foundation models</u> can be used as the basis for agents. Allen Institute for AI released an open-source vision-language model in 2024 ~~.~~ <u>[26] Nvidia released a framework for developers to use VLMs, LLMs and retrieval-augmented generation for building AI agents that can analyze images and videos, including [27] video search and video summarization</u> ~~.~~ <u>[28] Microsoft released a multimodal agent model – trained on</u> images, video, software <u>user interface interactions, and robotics</u> data – that the company claimed can <u>[29]</u> manipulate software and robots ~~.~~

### **Applications**

_<u>The Information</u>_ divided AI agents into seven archetypes: business-task agents, for acting within enterprise software; conversational agents, which act as chatbots for customer support; research agents, for querying and analyzing information (such as OpenAI Deep Research); analytics agents, for analyzing data to create reports; <u>software developer or coding agents (such as Cursor); domain-specific agents,</u> which include specific subject matter knowledge; and web browser agents (such as OpenAI Operator).[30]

<u>[31]</u> By mid-2025, AI agents were being used in <u>video game development</u> ~~,~~ <u>gambling</u> (including <u>sports [32] betting), cryptocurrency wallet</u> ~~<u>s</u>~~ <u>[32] (including cryptocurrency trading and meme coin</u> ~~<u>s</u>~~ <u>[33]) and social media</u> ~~.~~ <u>[34] In August 2025,</u> _<u>New York Magazine</u>_ described <u>software development</u> as the most definitive use of AI agents ~~.~~ <u>[35]</u> _The Information_ noted AI coding agents and customer support as the primary uses of AI by businesses by October 2025, although a decline in the expectations of AI capabilities was also <u>[36]</u> noted.

In November 2025, _The Wall Street Journal_ reported that few companies that deployed AI agents have <u>[37]</u> received a return on investment.

##### **Government**

Several government bodies in the United States and United Kingdom have deployed or announced the deployment of agents at the local and national level. The city of Kyle, Texas deployed an AI agent from Salesforce in March 2025 for 311 customer service ~~.~~ <u>[38]</u> In November 2025, the Internal Revenue Service