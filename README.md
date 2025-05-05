# Smartech SDK Integration Tool

A Python-based tool to automate the integration of Smartech SDK into Android projects.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/allenThomsonNetcore/smartech-android-integrator.git
cd smartech-android-integrator
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```


## Usage

1. Run the integration tool:
```bash
python -m src.main.integrator
```

2. Follow the interactive prompts:
   - Enter the path to your Android project directory
   - Enter your Smartech App ID
   - Choose whether to integrate Push SDK
   - If Push SDK is selected, choose whether to ask for push notification permission

## Features

- Automated integration of Smartech SDK
- Support for both Java and Kotlin projects
- Support for both .gradle and .gradle.kts files
- Interactive user prompts
- Detailed status updates during integration
- Push notification integration (optional)
- Deep link handling
- Backup configuration

## Project Structure

```
smartech-sdk-integrator/
├── src/
│   ├── application/    # Application class management
│   ├── deeplink/      # Deep link handling
│   ├── manifest/      # Android manifest modifications
│   ├── gradle/        # Gradle file management
│   ├── push/          # Push notification handling
│   ├── backup/        # Backup configuration
│   └── main/          # Main integration logic
└── README.md
```

## Requirements

- Python 3.6 or higher
- Android project directory
- Smartech App ID

## Contributing

We welcome contributions to improve this tool! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your PR:
- Follows the existing code style
- Includes tests for new features
- Updates documentation as needed
- Has a clear description of changes

For major changes, please open an issue first to discuss what you would like to change.

## Version B1.0.1