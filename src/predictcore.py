import numpy as np
import operator
from sklearn import svm
import os
from PIL import Image
import torch
from sklearn.model_selection import train_test_split,StratifiedKFold
import torchvision.transforms as transforms
from sklearn.ensemble import RandomForestClassifier,ExtraTreesClassifier,GradientBoostingClassifier,VotingClassifier
from scipy import stats
import itertools
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
def loadmodel():
    global model,device,transform
    model = torch.load(r'../model/2021-05-03-16-mobilenet_v2-1.7.1-model.pkl', map_location='cpu')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    transform = transforms.Compose([transforms.Resize(224), transforms.ToTensor(), ])
loadmodel()
def loaddata(train,value,imgsize=8):
    img_lst = []
    data_lst = []
    val_target_array = np.array([])
    val_img_lst = []
    val_data_lst = []
    target_array = np.array([])
    for a,b,c in os.walk(train):
        target = os.path.basename(a)
        if target.isdigit():
            for file in c:
                if file.endswith('.jpg'):
                    fname = os.path.join(a,file)
                    target_array = np.append(target_array,int(target))
                    img = Image.open(fname)
                    img_lst.append(img)
                    img = img.resize((imgsize,imgsize))
                    img = img.convert('L')
                    data_lst.append(np.array(img).reshape(-1))
    data_array = np.array(data_lst)
    for a,b,c in os.walk(value):
        target = os.path.basename(a)
        if target.isdigit():
            for file in c:
                if file.endswith('.jpg'):
                    fname = os.path.join(a,file)
                    val_target_array = np.append(val_target_array,int(target))
                    img = Image.open(fname)
                    val_img_lst.append(img)
                    img = img.resize((imgsize,imgsize))
                    img = img.convert('L')
                    val_data_lst.append(np.array(img).reshape(-1))
    val_data_array = np.array(val_data_lst)
    return img_lst,data_array,target_array,val_img_lst,val_data_array,val_target_array
class kmeans:
    def __init__(self,train,value):
        self.train = train
        self.value = value
        pass
    def classfy(self,x,data,target,k=10):
        dataSetSize = data.shape[0]
        diffMat = np.tile(x, (dataSetSize, 1)) - data
        sqDiffMat = diffMat**2
        sqDistances = sqDiffMat.sum(axis=1)
        distances = sqDistances**0.5
        sortedDistIndicies = distances.argsort()
        classCount = {}
        for i in range(k):
            voteIlabel = target[sortedDistIndicies[i]]
            classCount[voteIlabel] = classCount.get(voteIlabel, 0) + 1
        sortedClassCount = sorted(classCount.items(), key=operator.itemgetter(1), reverse=True)
        return sortedClassCount[0][0]
    def fit(self):
        self.trainset,self.traintarget = loaddata(self.train,self.value)[1:3]
    def predict(self,x):
        return np.array([self.classfy(i,self.trainset, self.traintarget) for i in x])

class mobilenet:
    def __init__(self,train,value):
        pass
    def classify(self,img):
        img = transform(img)
        img = img.unsqueeze(0)
        img = img.to(device)
        with torch.no_grad():
            py = model(img)
        pb=torch.nn.functional.softmax(py,dim=1)
        _, predicted = torch.max(pb,1)
        classIndex_ = predicted[0]
        return classIndex_.item()
    def predict(self,imglst):
        return np.array([self.classify(img) for img in imglst])


if __name__=='__main__':
    train = r'D:\code\py\SMFS\20210503-train-data\train'
    value = r'D:\code\py\SMFS\20210503-train-data\val'
    img_lst,data_array,target_array,val_img_lst,val_data_array,val_target_array = loaddata(train,value)
    target_array,val_target_array = target_array.astype(int),val_target_array.astype(int)
    svc = svm.SVC(gamma=0.001, C=100)
    rf = RandomForestClassifier(n_estimators=1000,  max_features='sqrt', max_depth=None, min_samples_split=2, bootstrap=True, n_jobs=1, random_state=1)
    svc.fit(data_array,target_array)
    print("accuracy of svc is {}".format(sum(svc.predict(val_data_array)==val_target_array)/len(val_target_array)))
    rf.fit(data_array,target_array)
    print("accuracy of rf is {}".format(sum(rf.predict(val_data_array)==val_target_array)/len(val_target_array)))
    m = mobilenet(train,value)
    print("accuracy of mb is {}".format(sum(m.predict(val_img_lst)==val_target_array)/len(val_target_array)))
    #k = kmeans(train,value)
    #k.fit()
    boost = XGBClassifier()
    boost.fit(data_array,target_array)
    print("accuracy of boost is {}".format(sum(boost.predict(val_data_array)==val_target_array)/len(val_target_array)))
    lg = LogisticRegression(max_iter=50000)
    lg.fit(data_array,target_array)
    print("accuracy of lg is {}".format(sum(lg.predict(val_data_array)==val_target_array)/len(val_target_array)))
    svc_re = svc.predict(val_data_array)
    rf_re = rf.predict(val_data_array)
    m_re = m.predict(val_img_lst)
    boost_re = boost.predict(val_data_array)
    lg_re = lg.predict(val_data_array)
    lst_re = [svc_re,rf_re,m_re,boost_re,lg_re]
    lst_blend = []
    score_max = 0
    weight_max = np.array([0,0,0,0,0])
    for weight in itertools.product(np.arange(7),np.arange(7),np.arange(7),np.arange(7),np.arange(7)):
        #weight = np.random.randint(0,10,size=(5))
        #weight = [1,3, 6, 5, 9]
        weight = np.array(weight)
        if np.sum(weight)==0 or weight.min()!=1 and np.sum(weight%weight.min())==0:
            continue
        for i in range(len(weight)):
            for n in range(weight[i]):
                lst_blend.append(lst_re[i])
        
        blendtrain = np.dstack(lst_blend)[0].astype(np.int)
        score = sum(np.array([stats.mode(i)[0][0] for i in blendtrain])==val_target_array)/len(val_target_array)
        if score>score_max:
            weight_max = weight
            score_max = score
            print(score_max)
            print(weight_max)
        if score>0.9:
            break
    print(score_max)
    print(weight_max)
    voting_clf = VotingClassifier(estimators=[
    ('log_clf', LogisticRegression(max_iter=50000)),
    ('svm_clf', svm.SVC(probability=True)),
('rf_clf',RandomForestClassifier(n_estimators=1000,  max_features='sqrt', max_depth=None, min_samples_split=2, bootstrap=True, n_jobs=1, random_state=1))]
        , voting='soft')
    voting_clf.fit(data_array, target_array)
    score = voting_clf.score(val_data_array, val_target_array)
    print("accuracy of voting is {}".format(score))
    '''
    blendtrain = np.dstack((svc.predict(val_data_array),
                            rf.predict(val_data_array),
                            m.predict(val_img_lst),
                            m.predict(val_img_lst),
                            k.predict(val_data_array),
                            lg.predict(val_data_array),
                            lg.predict(val_data_array),
                            lg.predict(val_data_array)))[0].astype(np.int)
    '''
    #print(sum(np.array([stats.mode(i)[0][0] for i in blendtrain])==val_target_array)/len(val_target_array))
    
    