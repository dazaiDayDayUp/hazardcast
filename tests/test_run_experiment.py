"""验证实验阶段如何运行和检查产物。"""

import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.run_experiment import load_config, run_stage, stage_command


class ExperimentStageTest(unittest.TestCase):
    def test_injects_time_list_into_config(self):
        """时刻清单应覆盖配置占位符，并记录实际清单路径。"""
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.yaml"
            times_path = root / "times.yaml"
            config_path.write_text("name: test\ntimes: ???\n", encoding="utf-8")
            times_path.write_text('times:\n  - "2021-02-02T00:00:00"\n', encoding="utf-8")

            config = load_config(config_path, times_path)

            self.assertEqual(list(config.times), ["2021-02-02T00:00:00"])
            self.assertEqual(config.time_list, str(times_path.resolve()))

    def test_builds_distributed_stage_command(self):
        """多进程阶段应通过 torch.distributed.run 在单节点启动。"""
        stage = {
            "script": "generate.py",
            "args": ["--config-name=taiwan"],
            "nproc_per_node": 2,
        }
        command = stage_command(stage)
        self.assertEqual(
            command,
            [
                sys.executable,
                "-m",
                "torch.distributed.run",
                "--standalone",
                "--nproc_per_node=2",
                "generate.py",
                "--config-name=taiwan",
            ],
        )

    def test_runs_in_stage_directory_and_preserves_argument_order(self):
        """配置选项应排在共用覆盖参数之前，产物应写入阶段目录。"""
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            script = run_dir / "stage.py"
            script.write_text(
                "import sys\n"
                "from pathlib import Path\n"
                "Path('args.txt').write_text('\\n'.join(sys.argv[1:]))\n"
                "print('阶段脚本已执行')\n",
                encoding="utf-8",
            )
            output = run_dir / "training" / "args.txt"
            stage = {
                "name": "training",
                "script": str(script),
                "args": ["--config-name=taiwan", "model.width=32"],
                "common_args": ["training.batch_size=1"],
                "outputs": [str(output)],
            }
            with redirect_stdout(StringIO()):
                run_stage(stage, run_dir, os.environ.copy())

            self.assertEqual(output.read_text().splitlines(), stage["args"] + stage["common_args"])
            self.assertIn("阶段脚本已执行", (output.parent / "运行.log").read_text(encoding="utf-8"))

    def test_missing_output_is_reported(self):
        """脚本退出成功但漏写产物时，这一阶段仍应失败。"""
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            script = run_dir / "stage.py"
            script.write_text("pass\n", encoding="utf-8")
            stage = {
                "name": "evaluation",
                "script": str(script),
                "args": [],
                "outputs": [str(run_dir / "evaluation" / "metrics.nc")],
            }
            with redirect_stdout(StringIO()), self.assertRaisesRegex(RuntimeError, "未生成预期产物"):
                run_stage(stage, run_dir, os.environ.copy())
