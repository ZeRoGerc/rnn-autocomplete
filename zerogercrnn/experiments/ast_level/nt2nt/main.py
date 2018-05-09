import torch

from zerogercrnn.experiments.ast_level.common import ASTMain
from zerogercrnn.experiments.ast_level.nt2nt.model import NT2NTBaseModel
from zerogercrnn.lib.utils import filter_requires_grad, setup_tensor
from zerogercrnn.lib.metrics import NonTerminalTerminalAccuracyMetrics
from zerogercrnn.lib.run import NetworkRoutine


def run_model(model, iter_data, hidden, batch_size):
    ((nt_input, t_input), (nt_target, t_target)), forget_vector = iter_data
    assert forget_vector.size()[0] == batch_size

    nt_input = setup_tensor(nt_input)
    t_input = setup_tensor(t_input)
    nt_target = setup_tensor(nt_target)
    t_target = setup_tensor(t_target)

    if hidden is None:
        hidden = model.init_hidden(batch_size=batch_size)

    model.zero_grad()
    nt_prediction, t_prediction, hidden = model(nt_input, t_input, hidden, forget_vector=forget_vector)

    return nt_prediction, t_prediction, nt_target, t_target, hidden


class ASTRoutine(NetworkRoutine):

    def __init__(self, model, batch_size, seq_len, nt_criterion, t_criterion, optimizers):
        super().__init__(model)
        self.model = self.network
        self.batch_size = batch_size
        self.seq_len = seq_len
        self.nt_criterion = nt_criterion
        self.t_criterion = t_criterion
        self.optimizers = optimizers

        self.hidden = None

    def calc_loss(self, nt_prediction, t_prediction, nt_target, t_target):
        nt_loss = self.nt_criterion(nt_prediction.permute(1, 2, 0), nt_target.transpose(1, 0))
        t_loss = self.t_criterion(t_prediction.permute(1, 2, 0), t_target.transpose(1, 0))

        return (nt_loss + t_loss) / 2

    def optimize(self, loss):
        # Backward pass
        loss.backward()

        torch.nn.utils.clip_grad_norm_(filter_requires_grad(self.model.parameters()), 5)
        # Optimizer step
        for optimizer in self.optimizers:
            optimizer.step()

    def run(self, iter_num, iter_data):
        nt_prediction, t_prediction, nt_target, t_target, hidden = run_model(model=self.model, iter_data=iter_data,
                                                                             hidden=self.hidden,
                                                                             batch_size=self.batch_size)
        self.hidden = hidden

        loss = self.calc_loss(nt_prediction, t_prediction, nt_target, t_target)
        if self.optimizers is not None:
            self.optimize(loss)

        return nt_prediction, t_prediction, nt_target, t_target


class NT2NTMain(ASTMain):

    def __init__(self, args):
        super().__init__(args)
        self.plotter = 'tensorboard_combined'

    def create_model(self, args):
        return NT2NTBaseModel(
            non_terminals_num=args.non_terminals_num,
            non_terminal_embedding_dim=args.non_terminal_embedding_dim,
            terminals_num=args.terminals_num,
            terminal_embeddings=self.terminal_embeddings,
            hidden_dim=args.hidden_size,
            num_layers=args.num_layers,
            dropout=args.dropout
        )

    def create_train_routine(self, args):
        return ASTRoutine(model=self.model, batch_size=args.batch_size, seq_len=args.seq_len,
                          nt_criterion=self.criterion, t_criterion=self.criterion, optimizers=self.optimizers)

    def create_validation_routine(self, args):
        return ASTRoutine(model=self.model, batch_size=args.batch_size, seq_len=args.seq_len,
                          nt_criterion=self.criterion, t_criterion=self.criterion, optimizers=None)

    def create_metrics(self, args):
        return NonTerminalTerminalAccuracyMetrics()
