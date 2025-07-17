# Decision: Choosing Content Understanding over LLM and Document Intelligence in Azure

## Introduction

In this document, we outline the reasons for selecting Content Understanding over Multimodal Large Language Models (MLLM) and Document Intelligence in Azure for our project. Content Understanding offers several advantages that align with our project requirements and goals.

## Justification

1. **Flexibility in Field Extraction**: Document Intelligence lacks the flexibility to extract fields based on their definitions, relying mainly on field IDs. This approach is suitable for highly structured files without images. However, we want to support processing raw documents that are very unstructured with no specific format; we also potentially want to extract information from images, which is supported by Content Understanding.

2. **Handling Diverse Data Formats**: Content Understanding provides a unified service for ingesting and transforming data of different modalities, including documents, images, videos, and audio. This capability allows us to streamline workflows and extract insights seamlessly from various data types.

3. **Improving Output Data Accuracy**: Content Understanding uses advanced AI techniques like intent clarification and a strongly typed schema to effectively parse large files and extract values accurately. This customization ensures high-quality output tailored to our specific needs.

4. **Reducing Costs and Accelerating Time-to-Value**: By using confidence scores to trigger human review only when necessary, Content Understanding minimizes the total cost of processing content. Integrating different modalities into a unified workflow and grounding the content when applicable allows for faster reviews and quicker time-to-value.

5. **Core Features and Advantages**:
    - **Multimodal Data Ingestion and Content Extraction**: Instantly extracts core content from various data types, including transcriptions, text, faces, and more.
    - **Data Enrichment**: Enhances content extraction results with additional features like layout elements, barcodes, figures in documents, speaker recognition, and diarization in audio.
    - **Schema Inferencing**: Offers prebuilt schemas and allows customization to extract exactly what is needed, generating task-specific representations like captions, transcripts, summaries, thumbnails, and highlights.
    - **Post Processing**: Uses generative AI tools to ensure the accuracy and usability of extracted information, providing confidence scores for minimal human intervention and enabling continuous improvement through user feedback.

6. **Challenges with LLM-based Field Extraction**:
    - **Size and Complexity of Prompts**: Managing prompts to accommodate variations can be difficult, resulting in a large number of prompts and associated costs.
    - **Inconsistent Results**: Results may vary across multiple runs of the same document, leading to reliability issues.
    - **Grounding**: Ensuring that values are accurately extracted and traceable to address issues with hallucination.
    - **Lack of Confidence Scores**: Absence of confidence scores makes it challenging to automate downstream processes.

In conclusion, Azure AI Content Understanding offers a more flexible, accurate, and cost-effective solution for our project needs compared to MLLM and Document Intelligence.
