"""验证 NGC CorrDiff 构造参数的兼容转换。"""

import unittest

from scripts.convert_corrdiff import compatible_args


class CorrDiffCompatibilityTest(unittest.TestCase):
    def test_maps_spatial_grid_to_current_song_unet(self):
        """两个旧模型都应由当前网络内部生成四个空间位置通道。"""
        for name, module, class_name in (
            ("regression", "modulus.models.diffusion.unet", "UNet"),
            ("diffusion", "modulus.models.diffusion.preconditioning", "EDMPrecondSR"),
        ):
            document = {
                "__module__": module,
                "__name__": class_name,
                "__args__": {
                    "img_resolution": 448,
                    "img_channels": 4,
                    "img_in_channels": 16,
                    "img_out_channels": 4,
                    "sigma_min": 0,
                    "sigma_max": float("inf"),
                    "sigma_data": 0.5,
                    "model_type": "SongUNet",
                    "embedding_type": "zero",
                },
            }
            with self.subTest(name=name):
                args = compatible_args(document, name)
                self.assertEqual(args["img_in_channels"], 16)
                self.assertEqual(args["model_type"], "SongUNetPosEmbd")
                self.assertEqual(args["gridtype"], "sinusoidal")
                self.assertEqual(args["N_grid_channels"], 4)
                if name == "regression":
                    self.assertNotIn("img_channels", args)
                    self.assertNotIn("sigma_min", args)
                    self.assertNotIn("sigma_max", args)
                    self.assertNotIn("sigma_data", args)
                else:
                    self.assertEqual(args["img_channels"], 4)
                    self.assertEqual(args["sigma_data"], 0.5)

    def test_rejects_unexpected_checkpoint(self):
        """不能把兼容转换应用到来源不同的模型。"""
        with self.assertRaisesRegex(ValueError, "预期的 NGC"):
            compatible_args(
                {"__module__": "other", "__name__": "UNet", "__args__": {}},
                "regression",
            )
