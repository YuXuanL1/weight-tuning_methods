# -*- coding: utf-8 -*-
"""新型演算法_hw4_110306085.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WmJNbr_6AnTT-VIljUkzOq-9i94YWffe

將輸入的手寫數字圖像（MNIST數據集中的數字圖像）分類為0到9之間的數字

regression or classification? -> classification

x:binary or real numbers? -> real numbers

how many y values? -> 10

y:binary or real numbers? -> real numbers
"""

import copy
import torch
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# 加載原始數據集
full_train_dataset = datasets.MNIST(root='./data', train=True, transform=transforms.ToTensor(), download=True)

# 划分訓練集和測試集
train_data, test_data = train_test_split(full_train_dataset, test_size=0.2, random_state=42)

# 創建數據加載器
train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
test_loader = DataLoader(test_data, batch_size=64, shuffle=False)

# 定義神經網路模型
class TwoLayerNN(torch.nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(TwoLayerNN, self).__init__()
        self.fc1 = torch.nn.Linear(input_size, hidden_size)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

"""###weight-tunung_EB (best code for hw1)"""

input_size = 28 * 28
hidden_size = 11
output_size = 10
learning_rate = 1e-3
num_epochs = 200

model_wt_EB = TwoLayerNN(input_size, hidden_size, output_size)

criterion = torch.nn.CrossEntropyLoss()

optimizer = torch.optim.Adam(model_wt_EB.parameters(), lr=learning_rate)

losses_wt_EB = []
acc_wt_EB = []

for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)

        # forward
        outputs = model_wt_EB(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        # backward
        loss.backward()

        # w adjustment
        optimizer.step()

    losses_wt_EB.append(loss.item())

    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = model_wt_EB(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_wt_EB.append(accuracy)
        print(f'Accuracy on the test set: {(100 * correct / total):.2f}%')

"""###**weight-tunung_EB + regularizing_EB**"""

learning_goal = 0.001
reg_lambda = 0.001

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model_wt_EB.parameters(), lr=learning_rate) #使用acceptable的model_wt_EB模型

# 儲存初始權重
initial_weights = {name: param.clone() for name, param in model_wt_EB.named_parameters()}

# 訓練模型
losses_r_EB = []
acc_r_EB = []
for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)
        outputs = model_wt_EB(images)
        reg_loss = sum(torch.sum(param ** 2) for param in model_wt_EB.parameters())
        loss = criterion(outputs, labels) + reg_lambda * reg_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if epoch % 200 == 199:
        if loss.item() < learning_goal:
            print("Learning goal achieved, stopping...")
            break
        else:
            print("Restoring initial weights...")
            for name, param in model_wt_EB.named_parameters():
                param.data = initial_weights[name].data
            break

    losses_r_EB.append(loss.item())
    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = model_wt_EB(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_r_EB.append(accuracy)
        print(f'Accuracy on the test set: {accuracy:.2f}%')

"""###weight-tunung_LG_UA"""

input_size = 28 * 28
hidden_size = 11
output_size = 10
learning_rate = 1e-3
learning_goal = 0.01  # 設定學習目標閾值

model_wt_LG_UA = TwoLayerNN(input_size, hidden_size, output_size)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model_wt_LG_UA.parameters(), lr=learning_rate)

losses_wt_LG_UA = []
acc_wt_LG_UA = []
previous_loss = float('inf')
learning_rate_threshold = 1e-5  # 學習率的閾值，用於決定是否終止訓練

epoch = 0
while True:
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)
        outputs = model_wt_LG_UA(images)
        loss = criterion(outputs, labels)

        # 動態調整學習率
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # 檢查是否達到學習目標
    if loss.item() < learning_goal:
        print(f"Learning goal achieved at Epoch [{epoch + 1}], Batch [{i + 1}], Loss: {loss.item():.4f}.")
        break

    # 根據損失歷史調整權重
    if loss.item() < previous_loss:
        # 更新模型參數
        previous_loss = loss.item()
        learning_rate *= 1.2  # 增加學習率
    else:
        # 檢查學習率閾值以決定進一步的操作
        if learning_rate > learning_rate_threshold:
            # 還原到先前的模型權重
            for param_group in optimizer.param_groups:
                for p in param_group['params']:
                    p.data = p.data.sub(learning_rate * 0.7 * p.grad.data)  # 使用降低的學習率更新權重
            optimizer.zero_grad()  # 重置梯度
            continue  # 重新開始訓練循環
        else:
            break  # 如果學習率太低，則停止訓練

    losses_wt_LG_UA.append(loss.item())
    print(f'Epoch [{epoch + 1}], Batch [{i + 1}], Loss: {loss.item():.4f}')

    if loss.item() < learning_goal or learning_rate <= learning_rate_threshold:
        break

    epoch += 1

    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = model_wt_LG_UA(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_wt_LG_UA.append(accuracy)
        print(f'Accuracy: {accuracy:.2f}%')

"""###**weight-tunung_LG_UA + regularizing_LG_UA**"""

reg_lambda = 0.001

losses_r_LG_UA = []
acc_r_LG_UA = []

def regularized_loss(outputs, labels, model):
    criterion = torch.nn.CrossEntropyLoss()
    standard_loss = criterion(outputs, labels)
    reg_loss = 0
    for param in model.parameters():
        reg_loss += torch.sum(param ** 2)
    total_loss = standard_loss + reg_lambda * reg_loss
    return total_loss

optimizer = torch.optim.Adam(model_wt_LG_UA.parameters(), lr=learning_rate)

epoch = 0
while True:
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)
        outputs = model_wt_LG_UA(images)
        loss = regularized_loss(outputs, labels, model_wt_LG_UA)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if loss.item() < previous_loss:
        previous_loss = loss.item()
        if loss.item() < learning_goal:
            print(f"Learning goal achieved with regularization at Epoch [{epoch + 1}], Loss: {loss.item():.4f}.")
            break
        else:
            learning_rate *= 1.2
    elif learning_rate > learning_rate_threshold:
        learning_rate *= 0.7
    else:
        break

    losses_r_LG_UA.append(loss.item())
    print(f'Epoch [{epoch + 1}], Loss: {loss.item():.4f}')
    epoch += 1

    with torch.no_grad():
      correct = 0
      total = 0
      for images, labels in test_loader:
        images = images.view(-1, 28 * 28)
        outputs = model_wt_LG_UA(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

      accuracy = (100 * correct / total)
      acc_r_LG_UA.append(accuracy)
      print(f'Accuracy on the test set: {accuracy:.2f}%')

"""###weight-tunung_EB_LG_UA"""

input_size = 28 * 28
hidden_size = 11
output_size = 10
learning_rate = 1e-3
num_epochs = 200
learning_goal = 0.05  # 學習目標，當訓練損失低於此值時停止訓練

model_wt_EB_LG_UA = TwoLayerNN(input_size, hidden_size, output_size)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model_wt_EB_LG_UA.parameters(), lr=learning_rate)

losses_wt_EB_LG_UA = []
acc_wt_EB_LG_UA = []
previous_loss = float('inf')
learning_rate_threshold = 1e-5  # 學習率的閾值，用於決定是否終止訓練

for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)
        outputs = model_wt_EB_LG_UA(images)
        loss = criterion(outputs, labels)

        # 檢查是否達到學習目標
        if loss.item() < learning_goal:
            print(f"Learning goal achieved at Epoch [{epoch + 1}], Batch [{i + 1}].")
            break

        if epoch >= num_epochs:
            print("Epoch limit reached. Stopping training.")
            break

        # 計算梯度並更新權重
        optimizer.zero_grad()
        loss.backward()

        with torch.no_grad():
            old_params = {}
            for name, param in model_wt_EB_LG_UA.named_parameters():
                old_params[name] = param.clone()

        optimizer.step()

        # New forward pass
        outputs = model_wt_EB_LG_UA(images)
        loss = criterion(outputs, labels)

        # 調整權重基於損失的變化
        if loss.item() < previous_loss:
            previous_loss = loss.item()
            learning_rate *= 1.2  # Increase learning rate
        else:
            # 檢查學習率閾值以決定進一步的操作
            if learning_rate > learning_rate_threshold:
                with torch.no_grad():
                    for name, param in model_wt_EB_LG_UA.named_parameters():
                        param.copy_(old_params[name])
                learning_rate *= 0.7  # Decrease learning rate
                continue  # 重新開始訓練循環
            else:
                break  # 如果學習率太低，則停止訓練

        losses_wt_EB_LG_UA.append(loss.item())
        print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')


    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = model_wt_EB_LG_UA(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_wt_EB_LG_UA.append(accuracy)
        print(f'Epoch [{epoch + 1}/{num_epochs}], Test Accuracy: {accuracy:.2f}%')

"""###**weight-tunung_EB_LG_UA + regularizing_EB_LG_UA**"""

initial_weights = {name: param.clone().detach() for name, param in model_wt_EB_LG_UA.named_parameters()}

losses_r_EB_LG_UA = []
acc_r_EB_LG_UA = []
reg_strength = 0.001

for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)
        outputs = model_wt_EB_LG_UA(images)
        loss = criterion(outputs, labels)

        if loss.item() < learning_goal:
            print(f"Learning goal achieved at Epoch [{epoch + 1}], Batch [{i + 1}].")
            break

        current_weights = {name: param.clone().detach() for name, param in model_wt_EB_LG_UA.named_parameters()}

        if epoch >= num_epochs:
            for name, param in model_wt_EB_LG_UA.named_parameters():
                param.data = initial_weights[name].data
            print(f"Maximum epochs reached. Loss: {loss.item():.4f}")
            break

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        with torch.no_grad():
            for name, param in model_wt_EB_LG_UA.named_parameters():
                if 'weight' in name:
                    loss += reg_strength * param.pow(2).sum()
            outputs = model_wt_EB_LG_UA(images)
            loss = criterion(outputs, labels)

        if loss.item() <= previous_loss:
            previous_loss = loss.item()
            learning_rate *= 1.2
        else:
            if learning_rate > learning_rate_threshold:
                for name, param in model_wt_EB_LG_UA.named_parameters():
                    param.data = initial_weights[name].data
                learning_rate *= 0.7
            else:
                break

    losses_r_EB_LG_UA.append(loss.item())
    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = model_wt_EB_LG_UA(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_r_EB_LG_UA.append(accuracy)
        print(f'Epoch [{epoch + 1}/{num_epochs}], Test Accuracy: {accuracy:.2f}%')

"""###**weight-tuning_EB + regularizing_DO_EB**"""

class DropoutTwoLayerNN(torch.nn.Module):
    def __init__(self, model, dropout_prob=0.5):
        super(DropoutTwoLayerNN, self).__init__()
        self.model = model
        self.dropout = torch.nn.Dropout(dropout_prob)  # 添加dropout


    def forward(self, x):
        x = self.model.fc1(x)
        x = self.model.relu(x)
        x = self.dropout(x)
        x = self.model.fc2(x)
        return x

dropout_prob = 0.5  # dropout的概率

# 初始化模型
do_model_wt_EB = DropoutTwoLayerNN(model_wt_EB, dropout_prob)

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(do_model_wt_EB.parameters(), lr=learning_rate)

losses_DOr_EB = []
acc_DOr_EB = []

for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)

        outputs = do_model_wt_EB(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()

        optimizer.step()

    losses_DOr_EB.append(loss.item())

    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = do_model_wt_EB(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_DOr_EB.append(accuracy)
        print(f'Accuracy on the test set: {(100 * correct / total):.2f}%')

"""###**weight-tuning_EB + regularizing_BN_EB**"""

class BN_TwoLayerNN(torch.nn.Module):
    def __init__(self, model):
        super(BN_TwoLayerNN, self).__init__()
        self.model = model  # 代入已有的模型
        self.bn = torch.nn.BatchNorm1d(model.fc1.out_features)

    def forward(self, x):
        x = self.model.fc1(x)
        # x = self.model.relu(x)
        x = self.bn(x)
        x = self.model.fc2(x)
        return x

learning_rate = 1e-3
num_epochs = 200
learning_goal = 0.05

losses_BNr_EB = []
acc_BNr_EB = []

bn_model_wt_EB = BN_TwoLayerNN(model_wt_EB)

criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(bn_model_wt_EB.parameters(), lr=learning_rate)

for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        images = images.view(-1, 28 * 28)

        outputs = bn_model_wt_EB(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    losses_BNr_EB.append(loss.item())
    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, 28 * 28)
            outputs = bn_model_wt_EB(images)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        accuracy = (100 * correct / total)
        acc_BNr_EB.append(accuracy)
        print(f'Accuracy on the test set: {accuracy:.2f}%')

        if loss.item() < learning_goal:
            print(f"Learning goal achieved. Loss: {loss.item():.4f}")
            break

"""###比較training losses和accuracy"""

plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(losses_wt_EB, label='wt_EB')
plt.plot(losses_r_EB, label='r_EB')
plt.plot(losses_wt_LG_UA, label='wt_LG_UA')
plt.plot(losses_r_LG_UA, label='r_LG_UA')
plt.plot(losses_wt_EB_LG_UA, label='wt_EB_LG_UA')
plt.plot(losses_r_EB_LG_UA, label='r_EB_LG_UA')
plt.plot(losses_DOr_EB, label='DOr_EB')
plt.plot(losses_BNr_EB, label='BNr_EB')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Losses')

plt.subplot(1, 2, 2)
plt.plot(acc_wt_EB, label='wt_EB')
plt.plot(acc_r_EB, label='r_EB')
plt.plot(acc_wt_LG_UA, label='wt_LG_UA')
plt.plot(acc_r_LG_UA, label='r_LG_UA')
plt.plot(acc_wt_EB_LG_UA, label='wt_EB_LG_UA')
plt.plot(acc_r_EB_LG_UA, label='r_EB_LG_UA')
plt.plot(acc_DOr_EB, label='DOr_EB')
plt.plot(acc_BNr_EB, label='BNr_EB')
plt.xlabel('Epoch')
plt.ylabel('Accuracy (%)')
plt.title('Test Accuracy')

# 添加圖例
plt.legend()
plt.show()

