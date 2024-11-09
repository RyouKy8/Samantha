# Samantha OS¹ (Her)

Samantha is an AI assistant inspired by the movie *Her*. This project is built to provide real-time voice interactions using the Realtime API and Chainlit. Samantha acts as an agent that calls various tools to handle user requests, such as querying stock prices, generating images, and creating Python scripts.

## Setup and Running

You can run Samantha either by setting up a virtual environment using `uv` or using Docker Compose. Note that setting up the environment variables is required in all cases.

### Option 1: Using Virtual Environment

1. **Clone the Repository**
   ```sh
   git clone https://github.com/jesuscopado/samantha-os1.git
   cd samantha-os1
   ```

2. **Set Up Virtual Environment**
   - Install `uv` package manager: [Installation Instructions](https://docs.astral.sh/uv/getting-started/installation/)
   - Create the virtual environment:
     ```sh
     uv sync
     ```
   - Activate the virtual environment:
     ```sh
     source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
     ```

3. **Environment Variables**
   - Create a `.env` file in the root directory by copying `.env.example` and updating it with your own keys.

4. **Run the Application**
   ```sh
   cd app
   chainlit run samantha.py
   ```

### Option 2: Using Docker Compose

1. **Environment Variables**
   - Create a `.env` file in the root directory by copying `.env.example` and updating it with your own keys.

2. **Build and Run with Docker Compose**
   - Make sure Docker and Docker Compose are installed.
   - Run the following command:
     ```sh
     docker-compose up --d
     ```

## Tools and Features

This project includes several powerful tools:

- **Stock Price Queries**: Using the `yfinance` package, Samantha can query the latest stock price information.
- **Plotly Charts**: Visualizations are created using Plotly to provide insights.
- **Image Generation**: Samantha can generate images using AI models through the Together API.
- **Browser Interaction**: Open web pages based on prompts.
- **Internet Search**: Samantha can perform internet searches via the Tavily API.
- **LinkedIn Post Drafting**: Create LinkedIn posts based on given topics using an AI model.
- **Python Script Generation**: Generate Python scripts on-demand based on user-provided topics.
- **Python File Execution**: Create and execute Python scripts directly from the assistant.

## License

This project is licensed under the MIT License.

---

¹ Samantha OS is inspired by the movie *Her*, but it is not affiliated with or endorsed by any related entities.
