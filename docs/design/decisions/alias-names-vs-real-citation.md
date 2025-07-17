# Adding Citation Information as a Context to LLM

## Problem Statement

Currently, the stringified JSON objects being sent as context to the LLM contain a significant amount of unnecessary data, which increases the size of the context and reduces the efficiency of the LLM. This includes fields that do not add meaningful value and verbose citation information that occupies a large portion of the context. These issues lead to increased token usage, higher computational costs, and potential degradation in the quality of the LLM's output.

The primary challenges include:

1. **Unnecessary Fields**:
   - Fields like `Type` and other unused data add noise to the context without contributing to the LLM's understanding.

2. **Verbose Citation Information**:
   - Citation data in `source_bounding_boxes` properties are often lengthy and filled with random numbers, making the context unnecessarily large.

3. **Inefficient Use of Resources**:
   - The large size of the context results in higher token usage, which increases computational overhead and costs.

4. **Reduced LLM Performance**:
   - The presence of irrelevant and verbose data can distract the LLM from focusing on the essential information, potentially leading to suboptimal results.

Addressing these issues is critical to improving the efficiency and effectiveness of the LLM interactions.

## Proposed Solution

To address these issues, we propose the following changes:

1. **Remove Unnecessary Fields**:
   - Eliminate fields like `Type` and other unused data to reduce noise in the LLM context.

2. **Replace Citation Information with Alias Names**:
   - Replace `source_document` and `source_bounding_boxes` with a single field containing an alias name in the format `CITE{collectionid}-{seq#}`.
   - This approach significantly reduces the size of the context while maintaining the necessary citation information. Our initial anaylsys shows 50% reduction in input and output tokens

3. **Cache Original Data**:
   - Cache the original tool call that retrieves the JSON content.
   - Generate a new, optimized JSON content by removing unwanted data and replacing citation information with alias names.
  
4. **Replace Alias Names with Original Citation Information**:
   - After we receive LLM response using formatted structre, we replace the alias names with the original citation information,

## Benefits

- **Reduced Input and Output Tokens**:
  - By eliminating unnecessary data and replacing verbose citation information, the input and output tokens are reduced by approximately 50%.

- **Improved LLM Performance**:
  - Less noisy data allows the LLM to focus on relevant information, potentially improving the quality of the generated results.

- **Efficient Use of Resources**:
  - Reducing the size of the context minimizes computational overhead and costs associated with LLM usage.

## Drawbacks

- **Loss of Detailed Citation Information**:
  - While alias names simplify the context, the detailed citation data is no longer directly available in the LLM input.

- **Additional Processing Overhead**:
  - The process of caching the original data and generating the optimized JSON file adds a layer of complexity to the system.

## Implementation Steps

1. **Cache Original Data**:
   - Cache the result of the tool call that retrieves the original JSON file.

2. **Generate Optimized JSON**:
   - Remove unnecessary fields like `Type`.
   - Replace `source_bounding_boxes` with an alias name in the format `CITE{collectionid}-{seq#}`.

3. **Send Optimized JSON to LLM**:
   - Use the optimized JSON file as the context for the LLM.

4. **Maintain Mapping for Alias Names**:
   - Keep a mapping of alias names to their original citation data for reference or restoration if needed.

## Conclusion

This approach provides a streamlined and efficient way to send context to the LLM by reducing noise and unnecessary data. While there are some trade-offs, the benefits of reduced token usage and improved LLM performance outweigh the drawbacks, making this a viable solution for optimizing LLM interactions.
