from pathlib import Path

import torch

from networks import TemporalCNN


class PhaseModel:
    def __init__(self, train=False, device=None, weights_dir=None):
        self.train = train
        self.only_temporal = True
        self.image_based = False
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        weights_root = Path(weights_dir) if weights_dir else Path(__file__).resolve().parent / "pretrained_weights"
        cnn_weight_path = weights_root / "cnn_checkpoint_best_acc.pth.tar"
        head_weight_path = weights_root / "head_checkpoint_best_acc.pth.tar"

        self.net = TemporalCNN(out_size=7, backbone="resnet50_gn", head="tcn").to(self.device)

        if self.only_temporal:
            for param in self.net.cnn.parameters():
                param.requires_grad = False

        if not self.image_based and cnn_weight_path.exists():
            checkpoint = torch.load(cnn_weight_path, map_location=self.device)
            self.net.cnn.load_state_dict(checkpoint["state_dict"])

        if head_weight_path.exists():
            checkpoint = torch.load(head_weight_path, map_location=self.device)
            self.net.load_state_dict(checkpoint["state_dict"])

        self.net.eval()

    def reset(self):
        if hasattr(self.net, "temporal_head") and hasattr(self.net.temporal_head, "reset"):
            self.net.temporal_head.reset()
