#!/usr/bin/env python

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any


@dataclass
class BNO055:
    # raw sensor data from BNO, resolution not applied
    a_raw: Tuple[int, int, int]
    g_raw: Tuple[int, int, int]
    m_raw: Tuple[int, int, int]
    # fusion output from BNO, resolution not applied
    euler_raw: Tuple[int, int, int]
    quaternion_raw: Tuple[int, int, int, int]
    lin_a_raw: Tuple[int, int, int]
    gravity_raw: Tuple[int, int, int]
    # raw sensor data from BNO, resolution applied
    a: Tuple[float, float, float]
    g: Tuple[float, float, float]
    m: Tuple[float, float, float]
    # fusion output from BNO, resolution applied
    euler: Tuple[float, float, float]
    quaternion: Tuple[float, float, float, float]
    lin_a: Tuple[float, float, float]
    gravity: Tuple[float, float, float]
    # temperature and status registers
    temp: int
    calib_stat: int
    st_result: int
    int_sta: int
    sys_clk_status: int
    sys_status: int
    # resolutions
    quaternion_resolution: float = 1. / 2 ** 14
    acceleration_resolution: float = 1. / 100.
    magnetometer_resolution: float = 1. / 16.
    gyroscope_resolution: float = 1. / 16.
    linear_acceleration_resolution: float = 1. / 100.
    gravity_resolution: float = 1. / 100.
    euler_resolution: float = 1. / 16.

    def __init__(self):
        pass

    def apply_resolution(self):
        self.a = tuple(el * self.acceleration_resolution for el in self.a_raw)
        self.m = tuple(el * self.magnetometer_resolution for el in self.m_raw)
        self.g = tuple(el * self.gyroscope_resolution for el in self.g_raw)
        self.quaternion = tuple(el * self.quaternion_resolution for el in self.quaternion_raw)
        self.lin_a = tuple(el * self.linear_acceleration_resolution for el in self.lin_a_raw)
        self.gravity = tuple(el * self.gravity_resolution for el in self.gravity_raw)
        self.euler = tuple(el * self.euler_resolution for el in self.euler_raw)


if __name__ == "__main__":
    # example client
    pass
