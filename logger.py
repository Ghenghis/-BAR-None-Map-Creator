import logging
import os
import pathlib # Added
import appdirs # Added

def setup_logger(log_filename="bar_map_creator.log"): # Renamed parameter for clarity
    logger_name = "BARMapCreator" # Application-wide logger name
    
    # Determine user-specific log directory using appdirs
    log_dir_path_str = appdirs.user_log_dir("BARMapCreator", "BARMapCreator") # appname, appauthor
    log_dir_path = pathlib.Path(log_dir_path_str)
    
    # Create the log directory if it doesn't exist
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Define the full log file path
    log_file_path = log_dir_path / log_filename
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Prevent adding multiple handlers if setup_logger is called more than once
    # or if other loggers (like SD7Handler) have added handlers to this logger.
    # We specifically want our FileHandler.
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file_path) for h in logger.handlers):
        # Remove other handlers if any, to ensure only our configured one is used for this logger's file output
        # For more complex scenarios, one might want to be more selective
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        fh = logging.FileHandler(log_file_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # Added %(name)s
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Optional: Add a StreamHandler for console output during development/debugging
        # if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        #     sh = logging.StreamHandler()
        #     sh.setLevel(logging.DEBUG) # Or INFO
        #     sh.setFormatter(formatter)
        #     logger.addHandler(sh)

    return logger
