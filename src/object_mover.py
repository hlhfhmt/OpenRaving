import numpy as np
import openravepy
import utils


class ObjectMover(object):
  def __init__(self, env):
    self.env = env
    self.robot = self.env.GetRobots()[0]
    self.manip = self.robot.GetActiveManipulator()
    self.col_free_grasping_pose_cache = {}

  def pickup(self, obj_to_pickup):
    pose, _ = self.get_grasping_pose(obj_to_pickup)
    self.robot.SetDOFValues(pose,
                            self.robot.GetActiveManipulator().GetArmIndices())
    self.robot.Grab(obj_to_pickup)

  def get_grasping_pose(self, obj_to_grasp, col_free=True, bad_bodies=None):
    obj_name = obj_to_grasp.GetName()

    cached_value = self.col_free_grasping_pose_cache.get(obj_name, None)
    if cached_value is None:
      # print "Collision free pose for object %s is not cached, \
      #        looking for a pose" % obj_name
      pose, collisions = self._get_min_col_grasping_pose(obj_to_grasp,
                                                         col_free,
                                                         bad_bodies)
      if pose is None:
        if col_free:
          e = ObjectMoveError("No collision free grasping pose found")
        else:
          e = ObjectMoveError("No grasping pose found")
        raise e
      # TODO: Enable caching later
      # self.col_free_grasping_pose_cache[obj_name] = pose
    else:
      # print "Collision free pose for object %s already cached" %  obj_name
      # pose = cached_value
      pass

    return pose, collisions

  def _get_min_col_grasping_pose(self, obj_to_grasp, col_free=True,
                                 bad_bodies=None):
    # generating grasps
    grasps = self._generate_grasps(obj_to_grasp)
    openravepy.raveLogInfo("I've got %d grasps" % len(grasps))
    if len(grasps) == 0:
      return None, []

    # open gripper when checking for collisions
    dof_orig = self.robot.GetActiveDOFValues()
    dof_copy = list(dof_orig)
    gripper_joint_index = self.robot.GetJoint('r_gripper_l_finger_joint').GetDOFIndex()
    dof_copy[gripper_joint_index] = 0.54
    self.robot.SetDOFValues(dof_copy)

    # remove obj_to_grasp from environment when checking for collisions
    self.env.Remove(obj_to_grasp)

    # finding collision free grasping pose
    if col_free:
      ik_options = openravepy.IkFilterOptions.CheckEnvCollisions
    else:
      ik_options = openravepy.IkFilterOptions.IgnoreEndEffectorCollisions
    
    best_pose = None
    min_collisions = []
    num_min_collisions = float('inf')
    for grasp in grasps:
      pose = self.manip.FindIKSolution(grasp, ik_options)

      if pose is None:
        continue

      self.robot.SetDOFValues(pose, self.robot.GetActiveManipulator().GetArmIndices());

      collisions = utils.get_all_collisions(self.robot, self.env)
      # make sure collisions don't include any bad bodies
      bad_body_exists = False
      for body in collisions:
        if body in bad_bodies:
          bad_body_exists = True
          break;
      if bad_body_exists:
        continue

      if col_free:
        best_pose = pose
        min_collisions = collisions
        break

      if len(collisions) < num_min_collisions:
        num_min_collisions = len(collisions)
        min_collisions = collisions
        best_pose = pose

    # restore removed obj_to_grasp and robot DOFs before returning
    self.env.AddKinBody(obj_to_grasp)
    self.robot.SetDOFValues(dof_orig)

    return best_pose, [obj.GetName() for obj in min_collisions]

  def _generate_grasps(self, obj, use_general_grasps=True):
    """
    Returns a list with all the valid grasps for object obj.

    Parameters:
    obj: blah
    
    Returns:
    List of Transformation matrices, one for each valid grasping pose.
    """    
    
    class _GraspOptions(object):
      def __init__(self):
        self.delta = 0.0
        self.normalanglerange = 0.0
        self.standoffs = [0]
        self.rolls = np.arange(0.49*np.pi, 0.51*np.pi, 0.25*np.pi)
        self.directiondelta = 0.0
        pass
    
    gmodel = openravepy.databases.grasping.GraspingModel(self.robot, obj)

    if use_general_grasps:
      gmodel.grasps = utils.side_cylinder_pre_grasps
    else:
      if not gmodel.load():
        openravepy.raveLogInfo("Generating grasping model...")
        gmodel.autogenerate(_GraspOptions())

    openravepy.raveLogInfo("Generating grasps")
    validgrasps, _ = gmodel.computeValidGrasps(checkcollision=False, 
                           checkik=True,
                           checkgrasper=False)
    np.random.shuffle(validgrasps)
    
    openravepy.raveLogInfo("Number of valid grasps: %d" % len(validgrasps))
    return [gmodel.getGlobalGraspTransform(grasp) for grasp in validgrasps]

class ObjectMoveError(Exception):
  pass