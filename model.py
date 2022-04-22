import torch
from torch import nn
import torchvision.models as models
from torchvision import datasets, transforms
from time import time

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])


class Model(nn.Module):
    def __init__(self, model, last_layer):
        super(Model, self).__init__()
        # lw_model = torch.nn.Sequential(*list(model.children())[:-1])
        final_layer = list(model.children())[-1]
        self.n_classes = final_layer._modules[list(final_layer._modules.keys())[-1]].out_features
        self.model = model
        # self.softmax = nn.Softmax(dim=1)
        self.fc_last = nn.Linear(in_features=self.n_classes, out_features=last_layer)
        # self.model = nn.Sequential(model, fc_last, activation_last)
        
    def forward(self, x):
        x = self.model(x)
        x = torch.softmax(x, dim=1)
        x = self.fc_last(x)
        x = torch.tanh(x)
        return x


if __name__ == '__main__':
    print(torch.hub.get_dir())
    x = torch.randn(size=(1, 3, 1280, 720))

    basic_model = models.mobilenet_v3_small(pretrained=False)
    model = Model(basic_model, 2)
    model.eval()
    # model.cuda()
    for i in range(5):
        t0 = time()
        # model(normalize(x.cuda()))
        model(normalize(x))
        print(1/(time()-t0))
        x = torch.randn(size=(1, 3, 1280, 720))

    

