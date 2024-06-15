import numpy as np
import math
import taichi as ti
import taichi.math as tm
from video_writer import VideoWriter
from vedo import Volume
import bencher as bch
import panel as pn
import pyvista as pv
from vedo import Plotter

# https://www.degeneratestate.org/posts/2017/May/05/turing-patterns/


@ti.data_oriented
class SweepTuring(bch.ParametrizedSweep):
    Du = bch.FloatSweep(default=0.160, bounds=(0.08, 0.40))
    Dv = bch.FloatSweep(default=0.08, bounds=(0.04, 0.10))
    feed = bch.FloatSweep(default=0.04, bounds=(0.03, 0.05))
    kill = bch.FloatSweep(default=0.062, bounds=(0.060, 0.064))

    rendermode = bch.IntSweep(default=0, bounds=(0, 4))

    bitrate = bch.FloatSweep(default=1000, bounds=(100, 2000))

    duration = bch.FloatSweep(default=40)

    video_wiggle = bch.FloatSweep(default=0.02)

    record_volume_vid = bch.BoolSweep(default=False)

    headless = False

    resolution = bch.IntSweep(default=100, bounds=(10, 200))

    vid = bch.ResultVideo()
    voxel = bch.ResultReference()
    vol_vid = bch.ResultVideo()

    def setup(self):
        ti.init(arch=ti.vulkan)

        self.pixels = ti.Vector.field(3, ti.f32, shape=(self.resolution, self.resolution))
        self.uv = ti.Vector.field(2, ti.f32, shape=(2, self.resolution, self.resolution))
        self.values = ti.Vector.field(1, ti.f32, shape=(self.resolution, self.resolution))

        uv_grid = np.zeros((2, self.resolution, self.resolution, 2), dtype=np.float32)
        uv_grid[0, :, :, 0] = 1.0
        np.random.seed(42)
        rand_rows = np.random.choice(range(self.resolution), 50)
        rand_cols = np.random.choice(range(self.resolution), 50)
        uv_grid[0, rand_rows, rand_cols, 1] = 1.0

        palette = ti.Vector.field(4, ti.f32, shape=(5,))
        palette[0] = [0.0, 0.0, 0.0, 0.3137]
        palette[1] = [1.0, 0.1843, 0.53333, 0.37647]
        palette[2] = [0.8549, 1.0, 0.53333, 0.388]
        palette[3] = [0.376, 1.0, 0.478, 0.392]
        palette[4] = [1.0, 1.0, 1.0, 1]

        self.palette = palette
        # uv_deep = deepcopy(uv_grid)
        self.uv.from_numpy(uv_grid)

    @ti.kernel
    def compute(self, phase: int, Du: float, Dv: float, feed: float, kill: float):
        for i, j in ti.ndrange(self.resolution, self.resolution):
            cen = self.uv[phase, i, j]
            lapl = (
                self.uv[phase, i + 1, j]
                + self.uv[phase, i, j + 1]
                + self.uv[phase, i - 1, j]
                + self.uv[phase, i, j - 1]
                - 4.0 * cen
            )
            du = Du * lapl[0] - cen[0] * cen[1] * cen[1] + feed * (1 - cen[0])
            dv = Dv * lapl[1] + cen[0] * cen[1] * cen[1] - (feed + kill) * cen[1]
            val = cen + 0.5 * tm.vec2(du, dv)
            self.uv[1 - phase, i, j] = val

    @ti.kernel
    def render(self):
        for i, j in self.pixels:
            value = self.uv[0, i, j].y
            color = tm.vec3(0)
            if value <= self.palette[0].w:
                color = self.palette[0].xyz

            for k in range(4):
                c0 = self.palette[k]
                c1 = self.palette[k + 1]
                if c0.w < value < c1.w:
                    a = (value - c0.w) / (c1.w - c0.w)
                    color = tm.mix(c0.xyz, c1.xyz, a)

            self.pixels[i, j] = color

    @ti.kernel
    def get_val(self):
        for i, j in self.pixels:
            self.values[i, j] = self.uv[0, i, j].y

    def __call__(self, **kwargs):
        self.update_params_from_kwargs(**kwargs)
        self.setup()
        gui = ti.GUI("turing", res=self.resolution, show_gui=not self.headless)
        vr = VideoWriter(gui)

        self.vid = bch.gen_video_path("turing")
        if self.record_volume_vid:
            vedo_vid = bch.VideoWriter("vedovid")
            self.vol_vid = vedo_vid.filename
            plt = Plotter(axes=7, offscreen=False, interactive=0, size=(600, 600))
            plt.azimuth(-45)
        stacked_volume = np.zeros(shape=(self.resolution, self.resolution, self.duration))
        substeps = 60
        i = 0
        for frame in range(self.duration):
            i = frame
            vr.update_gui(self.pixels)
            gui.set_image(self.pixels)
            self.get_val()
            stacked_volume[:, :, frame] = self.values.to_numpy().squeeze()
            if self.record_volume_vid:
                vol = Volume(stacked_volume[:, :, :frame])
                vol.mode(self.rendermode).cmap("jet")
                plt.add(vol)
                scale = self.video_wiggle
                camera_lerp = bch.lerp(frame, 0, self.duration, 0, math.pi * 2)
                plt.camera.Azimuth(math.sin(camera_lerp) * scale)
                plt.camera.Elevation(math.cos(camera_lerp) * scale)
                plt.show()
                vedo_vid.append(plt.screenshot(asarray=True))
                # video.add_frame()
                plt.clear()

            gui.show()
            for _ in range(substeps):
                self.compute(i % 2, self.Du, self.Dv, self.feed, self.kill)
                i += 1
            self.render()

        self.voxel = bch.ResultReference(stacked_volume, container=pyvista_volume_container)
        vr.write(self.vid, self.bitrate)

        if self.record_volume_vid:
            plt.close()
            plt.close_window()
            # video.close()
            vedo_vid.write()
        gui.close()

        return super().__call__()


def pyvista_volume_container(npdat, **kwargs):
    # vol = pv.wrap(npdat)
    # pn.extension('vtk')
    # return pn.pane.VTKVolume(npdat, display_slices=True)
    plotter = pv.Plotter()
    vol = pv.wrap(npdat)
    plotter.add_volume(vol)
    # plotter.add_volume_clip_plane(vol)

    return pn.panel(plotter.ren_win, orientation_widget=True, **kwargs)


if __name__ == "__main__":
    run_cfg = bch.BenchRunCfg()
    run_cfg.level = 4
    run_cfg.use_sample_cache = True
    run_cfg.run_tag = "13"
    bench = SweepTuring().to_bench(run_cfg)

    SweepTuring.param.Du.bounds = [0.13, 0.19]

    plot_kwargs = dict(width=600, height=600)
    # SweepTuring.param.Dv.bounds = [0.08, 0.09]

    row = pn.Row()
    bench.plot_sweep("turing", input_vars=[SweepTuring.param.Du], plot=False)
    # bench.report.append(bench.get_result().to_auto(**plot_kwargs))

    SweepTuring.param.Du.default = 0.145
    bench.plot_sweep("turing", input_vars=[SweepTuring.param.Dv], plot=False)
    # bench.report.append(bench.get_result().to_auto(**plot_kwargs))

    SweepTuring.param.Dv.default = 0.07
    bench.plot_sweep("turing", input_vars=[SweepTuring.param.feed], plot=False)
    bench.report.append(bench.get_result().to_auto(**plot_kwargs))

    # row.append(bench.get_result().to_auto(**plot_kwargs))

    SweepTuring.param.feed.default = 0.07
    bench.plot_sweep("turing", input_vars=[SweepTuring.param.kill], plot=False)
    # bench.report.append(bench.get_result().to_auto(**plot_kwargs))
    # row.append(bench.get_result().to_auto(**plot_kwargs))

    # bench.report.append(row)

    bench.report.show()

    exit()

    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.Du,SweepTuring.param.Dv])

    SweepTuring.param.Du.bounds = [0.13, 0.19]
    SweepTuring.param.Dv.bounds = [0.08, 0.09]
    run_cfg.level = 4
    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.Du,SweepTuring.param.Dv])

    run_cfg.level = 4

    SweepTuring.param.Du.default = 0.176
    SweepTuring.param.Dv.default = 0.0825
    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.feed,SweepTuring.param.kill])

    # SweepTuring.param.Du.default = 0.176
    # SweepTuring.param.Dv.default = 0.0825

    # bench.plot_sweep("turing",)

    SweepTuring.param.feed.default = 0.03
    SweepTuring.param.kill.default = 0.064

    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.Du,SweepTuring.param.Dv])
    SweepTuring.param.Du.bounds = None
    SweepTuring.param.Dv.bounds = None
    SweepTuring.param.feed.bounds = None
    SweepTuring.param.kill.bounds = None

    def box(name, center, width):
        var = bch.FloatSweep(default=center, bounds=(center - width, center + width))
        var.name = name
        return var

    wid = 0.001

    run_cfg.level = 2

    # bench.plot_sweep("turing",input_vars=[box("Du",0.176,wid),box("Dv",0.0825,wid),box("feed",0.03,wid),box("kill",0.064,wid)])

    # bench.plot_sweep("turing",input_vars=[box("Du",0.176,wid),box("Dv",0.0825,wid),box("feed",0.03,wid),box("kill",0.06,0.001)])

    # bench.plot_sweep("turing",input_vars=[box("Du",0.176,wid),box("Dv",0.00725,0.001),box("feed",0.03,wid),box("kill",0.06,0.001)])

    wid = 0.001
    run_cfg.level = 3

    bench.plot_sweep(
        "turing",
        input_vars=[box("Du", 0.176, wid), box("Dv", 0.00725, 0.001), box("feed", 0.03, wid)],
    )

    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.feed,SweepTuring.param.Dv])
    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.feed,SweepTuring.param.Dv])

    # SweepTuring.param.Dv.default = 0.0825

    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.feed,SweepTuring.param.kill])

    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.col])

    # bench.plot_sweep("turing",input_vars=[SweepTuring.param.bitrate])
    # bench.report.save_index()
    bench.report.show()
