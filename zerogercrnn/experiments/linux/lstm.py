import torch.nn as nn


class LSTMLinuxNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1):
        super(LSTMLinuxNetwork, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=num_layers, dropout=0.01)
        self.h2o = nn.Linear(hidden_size, output_size)
        self.softmax = nn.LogSoftmax()

        self.init_params()

    def init_params(self):
        for name, param in self.lstm.named_parameters():
            nn.init.uniform(param, -0.08, 0.08)
            # if 'bias' in name:
            #     nn.init.constant(param, 0.0)
            # elif 'weight' in name:
            #     nn.init.xavier_normal(param)

        for name, param in self.h2o.named_parameters():
            nn.init.uniform(param, -0.08, 0.08)

    def forward(self, input_tensor):
        """
        :param input_tensor: tensor of size [seq_len, batch_size, input_size]
        """
        output_tensor, hidden = self.lstm(input_tensor)

        sz = list(output_tensor.size())
        sz[-1] = self.output_size
        output_tensor = output_tensor.view(-1, self.hidden_size)
        output_tensor = self.h2o(output_tensor)
        output_tensor = self.softmax(output_tensor)
        output_tensor = output_tensor.view(sz)

        return output_tensor