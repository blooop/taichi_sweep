import bencher as bch
from taichi_sweep.turing_pattern import SweepTuring
from taichi_sweep.publisher import publish_args

if __name__ == "__main__":
    run_cfg = bch.BenchRunCfg()
    run_cfg.level = 2
    run_cfg.use_sample_cache = True
    bench = SweepTuring().to_bench(run_cfg)

    bench.plot_sweep(
        "turing",
        input_vars=["feed", bch.p("Du", [0.13, 0.19])],
        const_vars=dict(record_volume_vid=True),
    )

    # bench.report.publish(publish_args, "docs")
    bench.report.show()

