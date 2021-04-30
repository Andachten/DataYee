def classify0(inX, dataSet, labels, k):

    """
    参数:
    - inX: 用于分类的输入向量
    - dataSet: 输入的训练样本集
    - labels: 样本数据的类标签向量
    - k: 用于选择最近邻居的数目
    """

    # 获取样本数据数量
    dataSetSize = dataSet.shape[0]

    # 矩阵运算，计算测试数据与每个样本数据对应数据项的差值
    diffMat = np.tile(inX, (dataSetSize, 1)) - dataSet

    # sqDistances 上一步骤结果平方和
    sqDiffMat = diffMat**2
    sqDistances = sqDiffMat.sum(axis=1)

    # 取平方根，得到距离向量
    distances = sqDistances**0.5

    # 按照距离从低到高排序
    sortedDistIndicies = distances.argsort()
    classCount = {}

    # 依次取出最近的样本数据
    for i in range(k):
        # 记录该样本数据所属的类别
        voteIlabel = labels[sortedDistIndicies[i]]
        classCount[voteIlabel] = classCount.get(voteIlabel, 0) + 1

    # 对类别出现的频次进行排序，从高到低
    sortedClassCount = sorted(
        classCount.items(), key=operator.itemgetter(1), reverse=True)

    # 返回出现频次最高的类别
    return sortedClassCount[0][0]
img_lst = []
data_lst = []
import os
from PIL import Image
target_array = np.array([])
for a,b,c in os.walk(r'D:\code\py\SMFS\20210425-train-data-re1\train'):
    target = os.path.basename(a)
    if target.isdigit():
        for file in c:
            if file.endswith('.jpg'):
                fname = os.path.join(a,file)
                target_array = np.append(target_array,target)
                img = Image.open(fname)
                img = img.resize((8,8))
                img = img.convert('L')
                img_lst.append(np.array(img))
                data_lst.append(np.array(img).reshape(-1))
img_array = np.array(img_lst)
data_array = np.array(data_lst)
svc.fit(data_array,target_array)
val_img_lst = []
val_data_lst = []
import os
from PIL import Image
val_target_array = np.array([])
for a,b,c in os.walk(r'D:\code\py\SMFS\20210425-train-data-re1\val'):
    target = os.path.basename(a)
    if target.isdigit():
        for file in c:
            if file.endswith('.jpg'):
                fname = os.path.join(a,file)
                val_target_array = np.append(val_target_array,target)
                img = Image.open(fname)
                img = img.resize((8,8))
                img = img.convert('L')
                val_img_lst.append(np.array(img))
                val_data_lst.append(np.array(img).reshape(-1))
img_lst = []
data_lst = []
import os
from PIL import Image
target_array = np.array([])
for a,b,c in os.walk(r'D:\code\py\SMFS\20210425-train-data-re1\train'):
    target = os.path.basename(a)
    if target.isdigit():
        for file in c:
            if file.endswith('.jpg'):
                fname = os.path.join(a,file)
                target_array = np.append(target_array,target)
                img = Image.open(fname)
                img = img.resize((128,128))
                img = img.convert('L')
                img_lst.append(np.array(img))
                data_lst.append(np.array(img).reshape(-1))
img_array = np.array(img_lst)
data_array = np.array(data_lst)
svc.fit(data_array,target_array)