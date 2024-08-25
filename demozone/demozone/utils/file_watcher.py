import os
import time
import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from demozone.utils import blobber

class Watcher:
    def __init__(self, directory_to_watch, process_function, session_id, max_speakers):
        self.DIRECTORY_TO_WATCH = directory_to_watch
        self.process_function = process_function
        self.session_id = session_id
        self.max_speakers = max_speakers
        self.observer = Observer()

    def run(self):
        event_handler = Handler(self.process_function, self.session_id, self.max_speakers)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    def __init__(self, process_function, session_id, max_speakers):
        self.process_function = process_function
        self.session_id = session_id
        self.max_speakers = max_speakers

    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"Received created event - {event.src_path}")
            if event.src_path.lower().endswith(('.wav', '.mp3', '.flac', '.aac', '.ogg', '.wma', '.m4a')):
                self.process_function(event.src_path, self.session_id, self.max_speakers)
            else:
                logging.warning(f"File is not an audio file: {event.src_path}")

def start_watching(directories_to_watch, process_functions, session_id, max_speakers):
    watchers = []
    for directory, process_function in zip(directories_to_watch, process_functions):
        watcher = Watcher(directory, process_function, session_id, max_speakers)
        watchers.append(watcher)
        watcher_thread = threading.Thread(target=watcher.run)
        watcher_thread.daemon = True
        watcher_thread.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        for watcher in watchers:
            watcher.observer.stop()
        for watcher in watchers:
            watcher.observer.join()