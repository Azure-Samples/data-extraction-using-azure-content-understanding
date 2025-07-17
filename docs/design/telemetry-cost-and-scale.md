# Telemetry Cost and Scalability Measures

- [Telemetry Cost and Scalability Measures](#telemetry-cost-and-scalability-measures)
  - [Goal](#goal)
  - [Strategies](#strategies)
    - [Set Sampling Percentage](#set-sampling-percentage)
    - [Set Retention Policies for Stored Telemetry Data](#set-retention-policies-for-stored-telemetry-data)
    - [Ensure Appropriate Log Levels](#ensure-appropriate-log-levels)
    - [Set Log Rotation Policies](#set-log-rotation-policies)
    - [Monitoring Alarms](#monitoring-alarms)

## Goal

Keeping track of telemetry data and costs is essential to maintain scalability and control expenses. As user numbers grow, planning ahead can prevent sudden cost increases and ensure resources are used effectively. This document offers practical tips and strategies to achieve this.

## Strategies

You can monitor current telemetry usage information in the Log Analytics workspace resource under **Settings** > **Usage and estimated costs**. From here, you can view data ingestion trends, costs, and other telemetry metrics in order to optimize data storage and costs.

### Set Sampling Percentage

Sampling helps reduce telemetry data volume while maintaining meaningful insights. Currently, all types of events are being captured.

These are the potential sampling methods at the SDK level:

- Fixed Sampling: Provides consistent sampling decisions across services based on a fixed percentage. It is supported by OpenTelemetry and ensures interoperability with applications using the Application Insights Classic API SDKs.
- Adaptive Sampling: Dynamically adjusts sampling based on traffic volume. Not yet adopted in OpenTelemetry but available in classic Application Insights SDK.

The recommendation is, given the Function App's low traffic and use of the classic Application Insights SDK:

- Use **Adaptive Sampling** with a sampling percentage range of **20%-80%** to dynamically adjust data collection based on traffic volume and optimize costs. This approach anticipates an increase in users and traffic in the coming months.
- Set a maximum limit of 5 telemetry items per second to prevent excessive data ingestion during high traffic periods.

Additionally, **requests** and **exceptions** should always be captured without sampling to ensure critical data is logged.

Here is an example of the `host.json` configuration:

```json
{
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 5,
        "minSamplingPercentage": 20,
        "maxSamplingPercentage": 80,
        "excludedTypes": "Request;Exception",
      }
    }
  }
}
```

Additional configuration options for telemetry sampling can be found in the [official Azure documentation](https://learn.microsoft.com/en-us/previous-versions/azure/azure-monitor/app/sampling-classic-api)

### Set Retention Policies for Stored Telemetry Data

By default, data in a Log Analytics workspace is retained for 30 days, except for log tables, which have a 90-day default retention. Key log tables include:

- `AppAvailabilityResults`
- `AppBrowserTimings`
- `AppDependencies`
- `AppExceptions`
- `AppEvents`
- `AppMetrics`
- `AppPageViews`
- `AppPerformanceCounters`
- `AppRequests`
- `AppSystemEvents`
- `AppTraces`

To support compliance and long-term trend analysis, we propose extending the retention period for log tables to 180 days. This ensures sufficient data for monitoring, troubleshooting, and deeper insights.

### Ensure Appropriate Log Levels

To ensure appropriate logging across environments, we can implement a configuration  that dynamically sets log levels based on the environment.

- DEV: Use lower log levels to capture detailed diagnostic information for troubleshooting. Recommend the following logging configuration in the `host.dev.json`:

    ```json
    {
      "logging": {
        "logLevel": {
          "default": "Debug",
          "Function": "Debug",
          "Host": "Debug",
          "Worker": "Debug"
        }
      }
    }
    ```

- UAT: Use higher log levels to simulate production-like behavior while capturing essential operational data. Recommend the following logging configuration in the `host.uat.json`:

    ```json
    {
      "logging": {
        "logLevel": {
          "default": "Information",
          "Function": "Warning",
          "Host": "Error",
          "Worker": "Information"
        }
      }
    }
    ```

For more details on configuring log levels in Azure Function Apps, refer to the [official Azure documentation](https://learn.microsoft.com/en-us/azure/azure-functions/configure-monitoring?tabs=v2#configure-log-levels)

### Set Log Rotation Policies

In the application logs, we use a mixed approach for log management:

- **SemanticKernel Implementation**: Uses OpenTelemetry to export logs, spans, and metrics efficiently:
  - Logs: Exported using `BatchLogRecordProcessor`.
  - Spans: Exported using `BatchSpanProcessor`.
  - Metrics: Exported using `PeriodicExportingMetricReader`.
  - Telemetry data is exported under the following conditions:
    - **Schedule Delay**: Exports occur every 5 seconds if the queue is not full.
    - **Batch Size**: Exports occur when the queue reaches a batch size of 512 log records.

- **Rest of the Function App**: Utilizes  Application Insights with auto-instrumentation for logging:
  - Custom log rotation is not required for telemetry data exported to Application Insights, as it is automatically managed by the service.

### Monitoring Alarms

To ensure effective monitoring, we recommend setting up alarms in the Log Analytics workspace. These alarms apply to both DEV and UAT environments:

- **Alarm on Failures**:

  - Soft threshold: Trigger an alert when failures reach 30 counts within a 15-minute period.
  - Hard threshold: Trigger an alert when failures exceed 100 counts within a 15-minute period.

- **Alarm on Dependency Health Checks**:
  - Trigger an alert after 3 consecutive dependency health check failures.

- **Alarm on total Cost of Resource Usage**:
  - Trigger an alert if resource costs increase by 50% compared to the baseline calculated over the past 180 days.
