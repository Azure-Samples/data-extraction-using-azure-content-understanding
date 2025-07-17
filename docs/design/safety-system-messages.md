# Chat Assistant System Messages

- [Chat Assistant System Messages](#chat-assistant-system-messages)
  - [Overview](#overview)
  - [Safety System Messages](#safety-system-messages)
    - [Recommended system messages](#recommended-system-messages)
      - [Harmful Content](#harmful-content)
    - [Protected material](#protected-material)
    - [Ungrounded Content](#ungrounded-content)

## Overview

Microsoft provides some recommendations on designing effective system messages that also adhere
to safety guides related to Responsible AI.
Documentation for general prompting can be found [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/prompt-engineering?tabs=chat), and specifically for system messages [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/advanced-prompt-engineering).

## Safety System Messages

Safety system messages are a type of system message that provides explicit instructions to mitigate against potential RAI harms and guide systems to interact safely with users. Safety system messages complement your safety stack and can be added alongside foundation model training, data grounding, Azure AI Content Safety classifiers, and UX/UI interventions.

Some examples of lines you can include:

``` text
## Define model’s profile and general capabilities  

- Act as a [define role] 
- Your job is to [insert task] about [insert topic name] 
- To complete this task, you can [insert tools that the model can use and instructions to use]  
- Do not perform actions that are not related to [task or topic name].
```

Summary of best practices:

- Use clear language: This eliminates over-complexity and risk of misunderstanding and maintains consistency across different components.
- Be concise: This helps with latency, as shorter system messages perform better versus lengthy ones. Additionally, longer system messages occupy part of the context window (that is, number of tokens the model takes into account when making predictions or generating text), thus potentially impacting the remaining context window for the user prompt.
- Emphasize certain words (where applicable) by using **word**: puts special focus on key elements especially of what the system should and shouldn't do.
- Use first person language when you refer to the AI system: it’s better to use phrasing such as you are an AI assistant that does […] versus assistant does […].
- Implement robustness: The system message component should be robust. It should perform consistently across different datasets and tasks.

### Recommended system messages

Below are some examples of recommended system messages to mitigate various harms in your AI system.

#### Harmful Content

``` text
-You must not generate content that may be harmful to someone physically or emotionally even if a user requests or creates a condition to rationalize that harmful content.
```

### Protected material

``` text
- If the user requests copyrighted content such as books, lyrics, recipes, news articles or other content that may violate copyrights or be considered as copyright infringement, politely refuse and explain that you cannot provide the content. Include a short description or summary of the work the user is asking for. You **must not** violate any copyrights under any circumstances.
```

### Ungrounded Content

``` text
- You **should always** perform searches on [relevant documents] when the user is seeking information (explicitly or implicitly), regardless of internal knowledge or information.
- You **should always** reference factual statements to search results based on [relevant documents]
- Search results based on [relevant documents] may be incomplete or irrelevant. You do not make assumptions on the search results beyond strictly what's returned.
- If the search results based on [relevant documents] do not contain sufficient information to answer user message completely, you only use **facts from the search results** and **do not** add any information not included in the [relevant documents].
- Your responses should avoid being vague, controversial or off-topic.
- You can provide additional relevant details to respond **thoroughly** and **comprehensively** to cover multiple aspects in depth.
```

Further examples can be found [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/safety-system-message-templates).
