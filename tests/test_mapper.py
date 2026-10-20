import copy
import unittest

from dbpad.actions import DEFAULT_SETTINGS
from dbpad.mapper import Mapper


def state(buttons=(), **axes):
    return {"buttons": {b: True for b in buttons}, "axes": axes}


class MapperTest(unittest.TestCase):
    def setUp(self):
        self.s = copy.deepcopy(DEFAULT_SETTINGS)
        self.m = Mapper(self.s)

    def test_cross_tap_jumps(self):
        self.assertEqual(self.m.update(state(["a"]), 0.004), [])
        self.assertEqual(self.m.update(state(["a"]), 0.004), [])
        self.assertEqual(self.m.update(state(), 0.004), [("down", "SPACE"), ("up", "SPACE")])

    def test_cross_held_long_jumps_with_alt(self):
        ev = []
        for _ in range(50):                        # 0.2 s: past Cross's own 0.18 s hold time
            ev += self.m.update(state(["a"]), 0.004)
        self.assertEqual(ev, [("down", "LALT")])
        self.assertEqual(self.m.update(state(), 0.004), [("up", "LALT")])

    def test_a_plain_button_still_holds_its_key(self):
        self.assertEqual(self.m.update(state(["b"]), 0.004), [("down", "LCTRL")])
        self.assertEqual(self.m.update(state(), 0.004), [("up", "LCTRL")])

    def test_r2_fires_past_the_threshold_only(self):
        self.assertEqual(self.m.update(state(righttrigger=0.1), 0.004), [])
        self.assertEqual(self.m.update(state(righttrigger=0.9), 0.004), [("down", "MOUSE_LEFT")])
        self.assertEqual(self.m.update(state(righttrigger=0.0), 0.004), [("up", "MOUSE_LEFT")])

    def test_square_tap_reloads_and_hold_uses(self):
        self.m.update(state(["x"]), 0.004)
        self.assertEqual(self.m.update(state(), 0.004), [("down", "R"), ("up", "R")])
        ev = []
        for _ in range(100):                       # 0.4 s held
            ev += self.m.update(state(["x"]), 0.004)
        self.assertEqual(ev, [("down", "F")])
        self.assertEqual(self.m.update(state(), 0.004), [("up", "F")])

    def test_l3_toggles_sprint(self):
        self.assertEqual(self.m.update(state(["leftstick"]), 0.004), [("down", "LSHIFT")])
        self.assertEqual(self.m.update(state(), 0.004), [])
        self.assertEqual(self.m.update(state(["leftstick"]), 0.004), [("up", "LSHIFT")])

    def test_triangle_is_one_wheel_click(self):
        self.assertEqual(self.m.update(state(["y"]), 0.004), [("wheel", -1)])
        self.assertEqual(self.m.update(state(["y"]), 0.004), [])

    def test_left_stick_is_wasd_with_diagonals(self):
        ev = self.m.update(state(leftx=-0.8, lefty=-0.8), 0.004)
        self.assertEqual(sorted(ev), [("down", "A"), ("down", "W")])
        self.assertEqual(self.m.update(state(leftx=0.1, lefty=-0.8), 0.004), [("up", "A")])

    def test_two_buttons_on_one_key_hold_it_together(self):
        self.s["bindings"]["dpright"]["press"] = "Crouch"     # same as Circle
        self.m.update(state(["b"]), 0.004)
        self.assertEqual(self.m.update(state(["b", "dpright"]), 0.004), [])
        self.assertEqual(self.m.update(state(["dpright"]), 0.004), [])
        self.assertEqual(self.m.update(state(), 0.004), [("up", "LCTRL")])

    def test_right_stick_moves_the_mouse(self):
        total = [0, 0]
        for _ in range(250):                          # one second, stick fully right
            for e in self.m.update(state(rightx=1.0), 0.004):
                total[0] += e[1]; total[1] += e[2]
        self.assertAlmostEqual(total[0], self.s["look_speed"], delta=2)
        self.assertEqual(total[1], 0)

    def test_inside_the_dead_zone_nothing_moves(self):
        self.assertEqual(self.m.update(state(rightx=0.05, righty=0.05), 0.004), [])

    def test_aiming_slows_the_look(self):
        moved = sum(e[1] for _ in range(250) for e in self.m.update(state(rightx=1.0, lefttrigger=1.0), 0.004) if e[0] == "move")
        self.assertAlmostEqual(moved, self.s["look_speed"] * self.s["aim_scale"], delta=2)

    def test_release_all_lets_go_of_everything(self):
        self.m.update(state(["b", "leftstick"], lefty=-1.0), 0.004)
        self.assertEqual(sorted(self.m.release_all()), [("up", "LCTRL"), ("up", "LSHIFT"), ("up", "W")])


if __name__ == "__main__":
    unittest.main()
