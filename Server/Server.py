from WhisperLive import TranscriptionServer
import argparse

if __name__ == "__main__":
    server = TranscriptionServer(use_vad=True,denoise=True,hotwords=['ansh'],model_list=["whisper_tiny_ct","tiny"])
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p',
                        type=int,
                        default=9090,
                        help="Websocket port to run the server on.")
    args = parser.parse_args()
    server.run(
        "0.0.0.0",
        port=args.port)