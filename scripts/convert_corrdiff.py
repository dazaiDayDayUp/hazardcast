"""将 NGC CorrDiff 旧版模型转换为当前 PhysicsNeMo 兼容格式。"""

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path

import torch

from physicsnemo.diffusion.preconditioners import EDMPrecondSR
from physicsnemo.models.diffusion_unets import CorrDiffRegressionUNet


MODELS = {
    "regression": (
        "modulus.models.diffusion.unet",
        "UNet",
        CorrDiffRegressionUNet,
    ),
    "diffusion": (
        "modulus.models.diffusion.preconditioning",
        "EDMPrecondSR",
        EDMPrecondSR,
    ),
}


def compatible_args(document, name):
    """把旧版构造参数映射到内部生成位置编码的当前模型。"""
    module, class_name, _ = MODELS[name]
    if document["__module__"] != module or document["__name__"] != class_name:
        raise ValueError(f"{name} 不是预期的 NGC CorrDiff 模型")
    args = document["__args__"].copy()
    if args["img_in_channels"] != 16 or args["img_out_channels"] != 4:
        raise ValueError(f"{name} 的通道数与正式 CorrDiff 台湾模型不一致")
    if name == "regression":
        args.pop("img_channels")
        for key in ("sigma_min", "sigma_max", "sigma_data"):
            args.pop(key)
    args.update(
        model_type="SongUNetPosEmbd",
        gridtype="sinusoidal",
        N_grid_channels=4,
    )
    return args


def convert(source_dir, output_dir):
    """逐个转换模型，并记录来源校验值和张量数量。"""
    output_dir.mkdir(parents=True)
    report = {"grid_order": ["sin(x)", "sin(y)", "cos(x)", "cos(y)"], "models": {}}
    for name, (_, _, model_class) in MODELS.items():
        source = source_dir / f"{name}.mdlus"
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        with tarfile.open(source) as archive:
            document = json.load(archive.extractfile("args.json"))
            state = torch.load(
                io.BytesIO(archive.extractfile("model.pt").read()),
                map_location="cpu",
                weights_only=True,
            )
        args = compatible_args(document, name)
        model = model_class(**args)
        model.load_state_dict(state, strict=True)
        output = output_dir / f"{name}.mdlus"
        model.save(output)
        report["models"][name] = {
            "source": str(source),
            "source_sha256": digest,
            "tensor_count": len(state),
            "output": str(output),
        }
        print(f"已转换 {name}：{len(state)} 个张量", flush=True)
    (output_dir / "转换记录.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="NGC 原始模型目录")
    parser.add_argument("output", type=Path, help="兼容模型输出目录")
    args = parser.parse_args()
    convert(args.source, args.output)
