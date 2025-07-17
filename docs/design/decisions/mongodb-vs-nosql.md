# Decision: Choosing CosmosDB MongoDB API over CosmosDB NoSQL API

## Introduction

In this document, we outline the reasons for selecting CosmosDB MongoDB API over CosmosDB NoSQL API for our project. The MongoDB API offers several advantages that align with our project requirements and goals.

## Justification

### 1. Rich Query Language

The MongoDB API offers a powerful and expressive query language that supports a wide range of operations, including filtering, sorting, and aggregations. This rich query capability allows us to perform complex data retrieval and manipulation efficiently, which may be more cumbersome with the NoSQL API.

### 2. Advanced Features

The MongoDB API offers advanced features such as transactions, which ensure data consistency across multiple operations. These features enhance the functionality of our application and enable us to implement complex use cases efficiently, which may not be as straightforward with the NoSQL API.

### 3. Performance and Scalability

CosmosDB's MongoDB API is designed to provide high performance and scalability. It supports indexing, automatic scaling with no sharding, and other performance optimization techniques that ensure efficient data access and handling of large-scale data and traffic.

### 4. Handling Concurrent Transactions

#### CosmosDB MongoDB API

**Pros:**

- **Advanced Transactions:** The MongoDB API supports multi-document ACID transactions, which ensure data consistency across multiple operations. This is particularly useful for applications that require updating different fields from different lease documents with concurrent transactions.
- **Optimistic Concurrency Control:** MongoDB provides mechanisms for handling concurrent updates, such as optimistic concurrency control, which helps prevent conflicts and ensures data integrity.

**Cons:**

- **Performance Overhead:** The use of transactions can introduce some performance overhead, especially in highly concurrent environments. However, this is often outweighed by the benefits of data consistency and integrity.

#### CosmosDB NoSQL API

**Pros:**

- **High Throughput:** The NoSQL API is designed for high throughput and can handle a large number of concurrent operations efficiently. This can be beneficial for applications with high write and read demands.

**Cons:**

- **Limited Transaction Support:** The NoSQL API has limited support for multi-document transactions, which can be a drawback for applications that require complex transactional operations. Ensuring data consistency across multiple operations may require additional application logic.

### 5. Familiarity and Ease of Use

The MongoDB API provides a familiar interface for developers who have experience with MongoDB. This familiarity reduces the learning curve and allows our team to leverage existing MongoDB knowledge and skills, leading to faster development and fewer errors.

### 6. Cost Comparison for Specific Use Case

For a use case involving a 10GB transactional store with 100 reads per second and 1 write per second, and each document being 2MB in size, the cost comparison between CosmosDB NoSQL and MongoDB is as follows:

#### CosmosDB NoSQL API

**Cost:**

- Approximately $986 per month.

#### CosmosDB MongoDB API

**Cost:**

- Approximately $163 per month.

## Conclusion

Choosing CosmosDB MongoDB API over CosmosDB NoSQL API provides us with the flexibility, performance, and ease of use needed to build a robust and efficient application. The MongoDB API's rich feature set and familiarity make it the ideal choice for our project's data management needs. Given our use case of managing raw documents with composite keys and the need to query based on any field, the MongoDB API offers the necessary capabilities to handle these requirements efficiently. The cost of using Cosmos DB with Mongo DB API is also another factor that has been considered in our design.

## References

- [Enhance Cost Optimization in Azure Cosmos DB Without Compromising Service](https://techcommunity.microsoft.com/blog/educatordeveloperblog/enhance-cost-optimization-in-azure-cosmos-db-without-compromising-service/4280200)
- [Estimate RU/s using the Azure Cosmos DB capacity planner - Azure Cosmos DB for NoSQL](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/estimate-ru-with-capacity-planner)
- [Cosmos DB Cost Calculator](https://cosmos.azure.com/capacitycalculator/)
- [What is Azure Cosmos DB for MongoDB (vCore architecture)?](https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/introduction)