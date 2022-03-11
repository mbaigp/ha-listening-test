import torch
from torch import nn
import torch.nn.functional as F
from torch.nn import Sequential, Linear, Dropout, ReLU, Sigmoid, Conv2d, ConvTranspose2d, BatchNorm1d, BatchNorm2d, LeakyReLU

class Flatten(nn.Module):
    def forward(self, input):
        return input.view(input.size(0), -1)


class UnFlatten(nn.Module):
    def forward(self, input, size=128):
        return input.view(input.size(0), size, 3, 3)


class ScaledDotProductAttention(nn.Module):
    ''' Scaled Dot-Product Attention '''

    def __init__(self, temperature, attn_dropout=0.1):
        super().__init__()
        self.temperature = temperature
        self.dropout = nn.Dropout(attn_dropout)

    def forward(self, q, k, v, mask=None):

        attn = torch.matmul(q / self.temperature, k.transpose(2, 3))

        if mask is not None:
            attn = attn.masked_fill(mask == 0, -1e9)

        attn = self.dropout(F.softmax(attn, dim=-1))
        output = torch.matmul(attn, v)

        return output, attn


class Conv_2d(nn.Module):
    def __init__(self, input_channels, output_channels, shape=3, stride=1, pooling=2):
        super(Conv_2d, self).__init__()
        self.conv = nn.Conv2d(input_channels, output_channels, shape, stride=stride, padding=shape//2)
        self.bn = nn.BatchNorm2d(output_channels)
        self.relu = nn.ReLU()
        self.mp = nn.MaxPool2d(pooling)
    def forward(self, x):
        out = self.mp(self.relu(self.bn(self.conv(x))))
        return out

class Conv_2d(nn.Module):
    def __init__(self, input_channels, output_channels, shape=3, pooling=2):
        super(Conv_2d, self).__init__()
        self.conv = nn.Conv2d(input_channels, output_channels, shape, padding=shape//2)
        self.bn = nn.BatchNorm2d(output_channels)
        self.relu = nn.ReLU()
        self.mp = nn.MaxPool2d(pooling)

    def forward(self, x):
        out = self.mp(self.relu(self.bn(self.conv(x))))
        return out


class Conv_emb(nn.Module):
    def __init__(self, input_channels, output_channels):
        super(Conv_emb, self).__init__()
        self.conv = nn.Conv2d(input_channels, output_channels, 1)
        self.bn = nn.BatchNorm2d(output_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.relu(self.bn(self.conv(x)))
        return out

class AudioEncoder(nn.Module):
    def __init__(self, size_w_rep=128):
        super(AudioEncoder, self).__init__()

        self.audio_encoder = Sequential(
            nn.BatchNorm2d(1), #256x48
            Conv_2d(1, 128, pooling=2),#128x24
            Conv_2d(128, 128, pooling=2), #64x12
            Conv_2d(128, 256, pooling=2), #32x6
            Conv_2d(256, 256, pooling=2), #16x3
            Conv_2d(256, 256, pooling=(1,2)), #8x3
            Conv_2d(256, 256, pooling=(1,2)), #4x3
            Conv_2d(256, 512, pooling=2), #2x1
            Flatten()
        )
        self.fc_audio = Sequential(
            Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            Dropout(0.5),
            Linear(512, size_w_rep),
            nn.LayerNorm(size_w_rep, eps=1e-6)
            )

    def forward(self, x):
        z = self.audio_encoder(x)
        z_d = self.fc_audio(z)
        return z, z_d


