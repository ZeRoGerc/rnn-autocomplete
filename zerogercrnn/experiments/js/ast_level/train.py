import torch
from torch.autograd import Variable

from zerogercrnn.lib.train.routines import NetworkRoutine


class ASTRoutine(NetworkRoutine):
    def __init__(self, network, criterion, optimizer=None, cuda=True):
        super(ASTRoutine, self).__init__(network)
        self.criterion = criterion
        self.optimizer = optimizer
        self.cuda = cuda and torch.cuda.is_available()

    def run(self, iter_num, n_input, n_target):
        """Input and target here are pair of tensors (N, T)"""
        non_terminal_input = Variable(n_input[0].unsqueeze(2))
        terminal_input = Variable(n_target[0].unsqueeze(2))

        non_terminal_target = Variable(n_target[0])
        terminal_target = Variable(n_target[1])

        if self.cuda:
            non_terminal_input = non_terminal_input.cuda()
            terminal_input = terminal_input.cuda()
            non_terminal_target = non_terminal_target.cuda()
            terminal_target = terminal_target.cuda()

        self.network.zero_grad()
        n_target = (non_terminal_target, terminal_target)
        n_output = self.network(non_terminal_input, terminal_input)

        loss = self.criterion(n_output, n_target)

        if self.optimizer is not None:
            loss.backward()
            self.optimizer.step()

        return loss.data[0]