import argparse
import uvicorn
from ai_gateway.config.settings import load_settings

def start_server(config_file: str | None = None):
    settings = load_settings()
    if config_file:
        settings.config_file = config_file
        print(f"Loading configuration from {config_file}")
        
    uvicorn.run(
        "ai_gateway.server.app:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )

def main():
    parser = argparse.ArgumentParser(description="AI Gateway CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start the gateway server")
    start_parser.add_argument("--config", type=str, help="Path to config file", default=None)

    args = parser.parse_args()

    if args.command == "start":
        start_server(args.config)

if __name__ == "__main__":
    main()
