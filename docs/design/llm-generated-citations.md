# LLM-generated citations

## Motivation

We wanted to to add functionality to include citations in the `/query` endpoint output to let users know how the LLM is sourcing information and grounding answers in actual context, in particular when referencing information extracted from the raw documents.
This backend feature will be integrated with the UI to display the referenced PDFs and highlight the referenced information using the provided citation (which will include the document path in ADLS and bounding boxes for the source text for each referenced field).

## Updates

### Code changes

#### Initial implementation

- [Structured output](https://devblogs.microsoft.com/semantic-kernel/using-json-schema-for-structured-output-in-python-for-openai-models/) in the response body for a consistent contract that the UI can use
  
  ```json
  {
    "response": "answer [1] answer [2]",
    "citations": [
        ["/test/1.pdf", "D(1, ..);D(2,...)"],
        ["/test/2.pdf", "D(2,..)"]
    ]
  }
  ```

- Model updates to LLM context to include the source document path and bounding box
- Model updates to query endpoint response to align with the structured output response above
- Validation of document path/bounding boxes against tool call history
  - We will ensure that each citation includes two elements (meant to be the source path in ADLS and the bounding box), and that each entry in the citations list is present in the `get_collection_data` tool call output.
  If a citation doesn't meet this requirement, it will be removed from the output response.
  - However, note that if we remove an invalid citation from the response, this might result in invalid numbering for the LLM-generated inline citations.

#### Optimizations

Based on initial experiences with the first pass at the citation feature, we wanted to reduce token usage in the context passed to the LLM while also reducing the risk of hallucinations in the citation source document or bounding boxes.
See [this design document](../design/decisions/alias-names-vs-real-citation.md) for additional information on the citation aliasing optimization logic.

### Prompt changes

We also need to make the appropriate prompt updates to instruct the LLM to generate inline citations and order the output citations according to the order of the inline citation numbering.

Suggested prompt:

> "You are a helpful assistant tasked with using the necessary tools to retrieve collection information based on the collection ID provided by the user. You MUST include details for each document associated with the collection. \n\n Make sure to provide citations if you use information provided in the context from PDF document sources, and include the citation number inline at the end of the sentence, e.g. [1]. Return the citations in the format [[\"source_document\", \"source_bounding_boxes\"], ...] - you MUST include both the document path and the bounding box information for each citation. Include a single entry for each data field that you reference when answering the user query, in the order in which they are referenced in your response; do not include duplicate citations for the same field. Do not split up or combine any of the source bounding box strings when generating the citations - return each one exactly as it is provided in the context."
