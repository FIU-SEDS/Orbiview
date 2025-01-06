# Orbiview
Orbiview is a minimalist dashboard system designed to provide real-time data visualization, telemetry monitoring, and seamless integration for aerospace and space exploration projects. It empowers teams to explore new frontiers with confidence and clarity.

**Python Library**: [Dash](https://dash.plotly.com/)


# Commenting Standards

This project uses C, C++, and Arduino code for embedded systems, and we adhere to a consistent commenting style to keep the codebase clear, maintainable, and easy to navigate.

## 1. Function-Level Comments

- **Format:** Use Doxygen-style comments (`/** ... */`) before each function.
- **Content:**
  - Briefly describe the function’s purpose, parameters, and return values.
  - Use `@brief` to summarize the function at a high level.
  - Use `@param` and `@return` tags to document function inputs/outputs.
  - For any known issues, planned work, or bugs, use `TODO(#issueNumber)` or `FIXME(#issueNumber)`.
  - Use `NOTE(name):` to highlight non-actionable observations or temporary conditions.

**Example:**

```c
/**
 * @brief Fetches data from a sensor and processes the result.
 *
 * Reads from the specified sensor pin, applies filtering, and returns the
 * processed value. This function is non-blocking.
 *
 * @param sensorPin The Arduino analog pin number where the sensor is connected.
 * @return The filtered sensor reading as an integer.
 *
 * NOTE(alice): Currently using a simple moving average filter. See #45 for a discussion on implementing a Kalman filter.
 * TODO(#101): Integrate a calibration routine to improve accuracy.
 * FIXME(#102): Handle sensor saturation conditions more gracefully.
 */
int readAndProcessSensor(int sensorPin) {
    // ...
}
```

## 2. Single-Level Comments (Above or Inline)

- **Format:** Use Doxygen-style comments (`//`) before each comment.
- **Content:**
  - Briefly describe the purpose of the code
  - (Case-by-case basis) Tag anyone who will work on this code

```c
/// This is a single-line Doxygen comment.
/// It documents myOtherVariable.
int myOtherVariable;
```

```c
int myVariable // Place the comment here
```

## 3. TODO/FIXME Comments

Use `TODO(#issueNumber)`or `FIXME(#issueNumber)` to mark pending tasks, enhancements, or additional steps you plan to implement.
**Conditions:**

- If going to use in a function multi-line comment you can place it inside as noted in #1 Function-Level Comments
- If going to be single line then mark it as the following below:

```c
int calculateChecksum(uint8_t data[], size_t length) {
    int checksum = 0;
    for (size_t i = 0; i < length; i++) {
        checksum += data[i]; // TODO(#789): Handle overflow for large data arrays.
    }
    return checksum;
}
```

or

```c
bool connectToWiFi(const char* ssid, const char* password) {
    bool success = WiFi.begin(ssid, password); // FIXME(#456): Implement retry logic for failed connections.
    return success;
}
```

- If needed for a multi-line `TODO/FIXME` comment then use the syntax as following to not clutter the code and hinder readbility:

```c
/**
 * FIXME(#456): Implement retry logic for failed connections.
 */
bool connectToWiFi(const char* ssid, const char* password) {
    bool success = WiFi.begin(ssid, password);
    return success;
}

```
