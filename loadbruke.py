# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 09:33:50 2021

@author: Zhengbin
"""
import os
import sys
import tempfile
import matlab
import matlab.engine

class MatlabFile(object):
    def __init__(self, work_dir: str, input_matlab_file_path: str):
        with open(input_matlab_file_path, 'rb') as f:
            data = f.read()
        self.temp_file = tempfile.NamedTemporaryFile(dir=work_dir, delete=False, suffix=".m")
        self.temp_file.write(data)
        self.temp_file.close()

        self.parent_dir = os.path.split(self.temp_file.name)[0]
        self.name = os.path.split(os.path.splitext(self.temp_file.name)[0])[1]

    def delete(self):
        """删除临时文件"""
        os.remove(self.temp_file.name)
def main():
    # 加载算法文件
    # a2_path = "C:\\algo_file\\model.m"
    a2_path = "model.m"
    algorithm_file = MatlabFile(
        work_dir=os.path.abspath("C:\\temp"),
        input_matlab_file_path=a2_path
    )

    userpath_file = MatlabFile(
        work_dir=os.path.abspath("C:\\temp"),
        input_matlab_file_path="userpath_modified.m"
    )

    # 初始化MATLAB引擎
    engine = matlab.engine.start_matlab()
    engine.userpath_modified(algorithm_file.parent_dir)  # 让matlab去哪里找算法文件
    userpath_file.delete()

    # 传入参数，并调用MATLAB算法
    u_real = matlab.double([[10]])
    y_real = matlab.double([[10]])
    F = matlab.double([[0.00000005]])
    Q = matlab.double([[0.00000002]])
    delta_y = matlab.double([[0]])

    try:
        result = getattr(engine, algorithm_file.name)(
            u_real, y_real, F, Q, delta_y, nargout=1
        )
    except matlab.engine.MatlabExecutionError as err:
        algorithm_file.delete()
        print(err, file=sys.stderr)
        exit()

    # 得到算法结果
    print(result)

    # 删除临时算法文件，释放资源
    algorithm_file.delete()
    engine.exit()