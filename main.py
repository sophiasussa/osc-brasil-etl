import logging
import os
import time
import threading
from pathlib import Path

import psutil
from dotenv import load_dotenv

from etl.extract import from_csv
from etl.transform import clean
from etl.load import (
    create_database_engine,
    create_tables,
    load_dataframe,
)


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


def monitor_memory(
    process: psutil.Process,
    stop_event: threading.Event,
    interval: float = 0.1,
) -> None:
    """Monitors and logs the peak RSS memory usage of the process."""

    peak_memory_mb = 0.0

    while not stop_event.is_set():
        memory_mb = process.memory_info().rss / (1024 ** 2)
        peak_memory_mb = max(peak_memory_mb, memory_mb)

        stop_event.wait(interval)

    # Capture one final measurement after the monitoring loop stops.
    memory_mb = process.memory_info().rss / (1024 ** 2)
    peak_memory_mb = max(peak_memory_mb, memory_mb)

    logging.info(
        "Pico de memória RSS do processo Python: %.2f MB",
        peak_memory_mb,
    )


def main() -> None:
    start_time = time.perf_counter()
    logging.info("Iniciando execução do pipeline ETL.")

    process = psutil.Process(os.getpid())
    stop_event = threading.Event()

    memory_thread = threading.Thread(
        target=monitor_memory,
        args=(process, stop_event, 1.0),
        name="memory-monitor",
        daemon=True,
    )

    memory_thread.start()

    try:
        load_dotenv()

        filepath = Path("data/osc.csv")
        db_url = os.getenv("DB_URL")

        if not db_url:
            raise ValueError("DB_URL não configurada.")

        # Extract
        extract_start = time.perf_counter()

        df = from_csv(filepath)

        extract_elapsed = time.perf_counter() - extract_start
        logging.info("Tempo de extração: %.2f segundos", extract_elapsed)

        logging.info(
            "Registros selecionados para teste: %d",
            len(df),
        )

        # Transform
        transform_start = time.perf_counter()

        df = clean(df)

        transform_elapsed = time.perf_counter() - transform_start
        logging.info(
            "Tempo de transformação: %.2f segundos",
            transform_elapsed,
        )

        logging.info(
            "DataFrame transformado com %d registros.",
            len(df),
        )

        # Load
        load_start = time.perf_counter()

        engine = create_database_engine(db_url)

        try:
            create_tables(engine)
            load_dataframe(df, engine)
        finally:
            engine.dispose()

        load_elapsed = time.perf_counter() - load_start
        logging.info("Tempo de carga: %.2f segundos", load_elapsed)

        logging.info("Pipeline executado com sucesso.")

    finally:
        stop_event.set()
        memory_thread.join()

        elapsed_time = time.perf_counter() - start_time

        logging.info(
            "Duração total do pipeline ETL: %.2f segundos (%.2f minutos).",
            elapsed_time,
            elapsed_time / 60,
        )


if __name__ == "__main__":
    main()
