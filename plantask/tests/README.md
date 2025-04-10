
```
# How to run the Tests with Pytest and Allure

This guide explains the steps and requirements for running tests using `pytest` and generating reports with `Allure`.

## Requirements

Before running the tests, ensure that you have all dependencies installed in your virtual environment, otherwise install them following the next command:

```bash
pip install -e .
```

This will download all requirements needed for the project :)

## Running Tests

Once the dependencies are installed, you can run the tests.

### Running Tests with Pytest

To run the tests with pytest, simply execute the following command from the root of the project:

```bash
pytest
```

If you want to run tests for specific files or functions, use:

```bash
pytest path/to/test_file.py
pytest path/to/test_file.py::test_function_name
```

## Generating Allure Report

To generate an Allure report, use the following steps:

1. Run the tests with the `--alluredir` flag to specify the directory where the Allure results will be stored.

   ```bash
   pytest --alluredir=allure-results
   ```

2. Generate the Allure report from the results:

   ```bash
   allure serve allure-results
   ```

   This will start a local server and open the Allure report in your default web browser. The report contains detailed information about the test execution, including success rates, test durations, and any failed test cases.

## Troubleshooting

- **Issue: No tests found**  
  If you see a message like "collected 0 items", make sure that your test functions or classes start with `test_` as per the default naming conventions of pytest.

- **Issue: Database connection errors**  
  Ensure the database URL is correct and the database server is accessible. If needed, check the connection using a simple SQL client or command-line tool.

- **Issue: Allure report not generated**  
  Make sure the `--alluredir` flag is used when running the tests. You can specify a custom directory for the results.

## EXTRA:

For more information on Allure and Pytest, visit the following resources:

- Pytest Documentation: [https://docs.pytest.org/en/stable/](https://docs.pytest.org/en/stable/)
- Allure Documentation: [https://allure.qatools.ru/](https://allure.qatools.ru/)
```

Just copy the above text and paste it into your `README.md` file, and it should render correctly on GitHub and other Markdown-compatible platforms.

Let me know if you need any further adjustments!