# In tests/test_sd7_handler.py
import pytest
import os
from sd7_handler import SD7Handler

def test_get_map_path_appends_sd7_extension():
    handler = SD7Handler(maps_directory="dummy_maps_dir") # Init with a dummy path
    map_name = "test_map"
    expected_path = os.path.join("dummy_maps_dir", "test_map.sd7")
    assert handler.get_map_path(map_name) == expected_path

def test_get_map_path_keeps_sd7_extension():
    handler = SD7Handler(maps_directory="dummy_maps_dir")
    map_name_with_ext = "another_map.sd7"
    expected_path = os.path.join("dummy_maps_dir", "another_map.sd7")
    assert handler.get_map_path(map_name_with_ext) == expected_path
