from turing_pattern import SweepTuring
import bencher as bch


if __name__ == "__main__":
    run_cfg = bch.BenchRunCfg()
    run_cfg.level = 2
    run_cfg.use_sample_cache = False
    run_cfg.run_tag = "best_2"
    run_cfg.plot_size = 600

    turing = SweepTuring()
    turing.headless = True
    bench = turing.to_bench(run_cfg)

    bench.worker_class_instance.param.record_volume_vid = True
    # SweepTuring().param.record_volume_vid=True

    args = {}
    result_vars = ["vid", "voxel"]
    result_vars = None

    const_vars = [["duration", 40], ["resolution", 200], ["feed", 0.3], ["record_volume_vid", True]]

    kwargs = dict(result_vars=result_vars, const_vars=const_vars)

    def publish_args(branch_name):
        return (
            "https://github.com/blooop/turing_sweep.git",
            f"https://github.com/blooop/turing_sweep/blob/{branch_name}",
        )

    # const_vars = [SweepTuring.param.feed.with_const(0.03),(SweepTuring.param.record_volume_vid,False),(SweepTuring.param.headless,True)]
    # bench.plot_sweep(input_vars=["feed","Dv"])

    # turing.param.feed.bounds=(0.3,0.8)
    bench.plot_sweep(input_vars=["feed"], **kwargs)
    bench.report.publish(publish_args, "docs")

    # bench.report.save_index()

    # v_list=[]
    # v_list.append([0.16,0.08,0.06,0.062])
    # v_list.append([0.175,0.0835,0.031,0.059])
    # v_list.append([0.176,0.0825,0.06,0.061])
    # v_list.append([0.16,0.085,0.03,0.062])

    # for v in v_list:

    #     SweepTuring.param.Du.bounds = None
    #     SweepTuring.param.Dv.bounds = None
    #     SweepTuring.param.feed.bounds = None
    #     SweepTuring.param.kill.bounds = None
    #     SweepTuring.param.record_volume_vid = True

    #     # res = bench.plot_sweep(
    #     #     input_vars=[],
    #     #     const_vars=[
    #     #         SweepTuring.param.Du.with_const(0.117),
    #     #         SweepTuring.param.Dv.with_const(0.0835),
    #     #         SweepTuring.param.feed.with_const(0.029),
    #     #         SweepTuring.param.kill.with_const(0.065),
    #     #     ],
    #     #     plot=False,
    #     # )
    #     print("vistli",v)

    #     # SweepTuring.param.Du.default = v[0]
    #     # SweepTuring.param.Dv.default = v[1]
    #     # SweepTuring.param.feed.default = v[2]
    #     # SweepTuring.param.kill.default = v[3]

    #     res = bench.plot_sweep(
    #         input_vars=[],
    #         const_vars=[
    #             SweepTuring.param.Du.with_const(v[0]),
    #             SweepTuring.param.Dv.with_const(v[1]),
    #             SweepTuring.param.feed.with_const(v[2]),
    #             SweepTuring.param.kill.with_const(v[3]),
    #         ],
    #         plot=False,
    #     )

    # for res in bench.results:
    # bench.report.append(res.to_auto(width=600, height=600))
    # bench.report.append(res.to_auto(width=300, height=300))

    # bench.report.append(res.to_auto())

    bench.report.show()
