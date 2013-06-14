import json
import trajoptpy
import openravepy
from collision_checker import CollisionChecker


class TrajectoryGenerator(object):
  def __init__(self, env, n_steps=10):
    self.env = env
    self.robot = self.env.GetRobots()[0]
    self.manip = self.robot.GetActiveManipulator()
    self.n_steps = n_steps
    self.collision_checker = CollisionChecker(self.env)

  def generate_traj(self, pos, rot,
                    init_joints=None,
                    collisionfree=True,
                    n_steps=None):
    if init_joints is None:
      mat = openravepy.matrixFromPose(rot + pos)

      if collisionfree:
        init_joints = self.manip.FindIKSolution(mat,
          openravepy.IkFilterOptions.CheckEnvCollisions)
      else:
        init_joints = self.manip.FindIKSolution(mat,
          openravepy.IkFilterOptions.IgnoreEndEffectorCollisions)

    request = {
      "basic_info" : {
        "n_steps" : self.n_steps if (n_steps is None) else n_steps,
        "manip" : "rightarm", # see below for valid values
        "start_fixed" : True # i.e., DOF values at first timestep are fixed based on current robot state
      },
      "costs" : [
      {
        "type" : "joint_vel", # joint-space velocity cost
        "params": {"coeffs" : [10]} # a list of length one is automatically expanded to a list of length n_dofs
        # Also valid: "coeffs" : [7,6,5,4,3,2,1]
      },
      {
        "type" : "collision",
        "name" : "col", # Shorten name so printed table will be prettier
        "params" : {
          "coeffs" : [20], # penalty coefficients. list of length one is automatically expanded to a list of length n_timesteps
          "dist_pen" : [0.00] # robot-obstacle distance that penalty kicks in. expands to length n_timesteps
        }
      },
      {
        "type" : "continuous_collision",
        "name" : "cont_col", # Shorten name so printed table will be prettier
        "params" : {
          "coeffs" : [20], # penalty coefficients. list of length one is automatically expanded to a list of length n_timesteps
          "dist_pen" : [0.025] # robot-obstacle distance that penalty kicks in. expands to length n_timesteps
        }
      }],
      "constraints" : [
      {
        "type" : "pose",
        "params" : {"xyz" : pos,
                    "wxyz" : rot,
                    "link": "r_gripper_tool_frame"}
      }],
      "init_info" : {
          "type" : "straight_line", # straight line in joint space.
          "endpoint" : init_joints.tolist()
      }
    }

    prob = trajoptpy.ConstructProblem(json.dumps(request), self.env)

    result = trajoptpy.OptimizeProblem(prob)
    traj = result.GetTraj()

    collisions = self.collision_checker.get_collisions(traj)
    if collisionfree and collisions:
      return None, collisions

    return traj, collisions

class GraspTrajectoryGenerator(object):
  def __init__(self, env, unmovable_objects=set(), approachdist=0.1):
    self.env = env
    self.robot = self.env.GetRobots()[0]
    self.manip = self.robot.GetActiveManipulator()
    self.unmovable_objects = unmovable_objects
    self.approachdist = approachdist
    self.pregrasp_trajectory_generator = TrajectoryGenerator(self.env)
    self.grasp_trajectory_generator = TrajectoryGenerator(self.env, 2)

  def generate_grasping_traj(self, obj, grasps, gmodel, collisionfree=True):
    for grasp in grasps:
      gmodel.setPreshape(grasp)

      # find trajectory to pregrasp
      Tgrasp1 = gmodel.getGlobalGraspTransform(grasp, collisionfree=True)

      approach = gmodel.getGlobalApproachDir(grasp) * self.approachdist
      Tgrasp1[0][3] -= approach[0]
      Tgrasp1[1][3] -= approach[1]
      Tgrasp1[2][3] -= approach[2]

      if collisionfree:
        init_joints1 = self.manip.FindIKSolution(Tgrasp1,
          openravepy.IkFilterOptions.CheckEnvCollisions)
      else:
        init_joints1 = self.manip.FindIKSolution(Tgrasp1,
          openravepy.IkFilterOptions.IgnoreEndEffectorCollisions)

      if init_joints1 is None:
        continue

      gripper_pose1 = openravepy.poseFromMatrix(Tgrasp1).tolist()
      xyz_target1 = gripper_pose1[4:7]
      # quaternions are rotated by pi/2 around y for some reason...
      quat_target1 = openravepy.quatMultiply(gripper_pose1[:4],
                                            (0.7071, 0, -0.7071, 0)).tolist()

      traj1, collisions1 = self.pregrasp_trajectory_generator.generate_traj(
        xyz_target1, quat_target1, init_joints1, collisionfree)
      if traj1 is None:
        continue

      # find trajectory to grasp
      orig_values = self.robot.GetDOFValues(
        self.robot.GetManipulator('rightarm').GetArmIndices())
      self.robot.SetDOFValues(traj1[-1],
        self.robot.GetManipulator('rightarm').GetArmIndices())
      self.env.Remove(obj)

      Tgrasp2 = gmodel.getGlobalGraspTransform(grasp, collisionfree=True)

      if collisionfree:
        init_joints2 = self.manip.FindIKSolution(Tgrasp2,
          openravepy.IkFilterOptions.CheckEnvCollisions)
      else:
        init_joints2 = self.manip.FindIKSolution(Tgrasp2,
          openravepy.IkFilterOptions.IgnoreEndEffectorCollisions)

      if init_joints2 is None:
        continue

      gripper_pose2 = openravepy.poseFromMatrix(Tgrasp2).tolist()
      xyz_target2 = gripper_pose2[4:7]
      # quaternions are rotated by pi/2 around y for some reason...
      quat_target2 = openravepy.quatMultiply(gripper_pose2[:4],
                                            (0.7071, 0, -0.7071, 0)).tolist()

      traj2, collisions2 = self.grasp_trajectory_generator.generate_traj(
        xyz_target2, quat_target2, init_joints2, collisionfree)

      # reset 
      self.robot.SetDOFValues(orig_values,
        self.robot.GetManipulator('rightarm').GetArmIndices())
      self.env.AddKinBody(obj)

      if traj2 is None:
        continue

      collisions = collisions1.union(collisions2)
      if self.unmovable_objects.intersection(collisions):
        continue

      return traj1.tolist() + traj2.tolist(), collisions

    return None, set()