# Copyright 2018 CNRS

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import time
from pinocchio import centerOfMass, forwardKinematics
from cop_des import CoPDes
from com_trajectory import ComTrajectory
from inverse_kinematics import InverseKinematics
from tools import Constant, Piecewise, Affine
from real_trajectory import RealTrajectory
from math import cos, sin

# Computes the trajectory of a swing foot.
#
# Input data are
#  - initial and final time of the trajectory,
#  - initial and final pose of the foot,
#  - maximal height of the foot,
#
# The trajectory is polynomial with zero velocities at start and end.
# The orientation of the foot is kept as in intial pose.
class SwingFootTrajectory(object):
    def __init__(self, t_init, t_end, init, end, height):
        assert(init[2] == end[2])
        self.t_init = t_init
        self.t_end = t_end
        self.height = height
        self.init = init
        self.end = end 

    def __call__(self, t):
        ti = self.t_init
        T = self.t_end - self.t_init
        x1 = self.end[0]
        x0 = self.init[0]

        y0= self.init[1]
        y1=self.end[1]

        z0= self.init[2]
        h = self.height + z0

        #---------Parameters of x function-----------
        a0 = x0
        a1 = 0
        a2 = -3 * (x0-x1)/T**2
        a3 = 2 * (x0-x1)/T**3
        
        #---------x calculus------------------------
        x = a3 * (t-ti)**3 + a2 * (t-ti)**2 + a1*(t-ti) + a0
        #---------Parameters of z function-----------
        b0 = z0
        b1 = 0 
        b4 = (16*(h-z0))/T**4
        b2 = b4*T**2
        b3 = -2*b4*T
        '''b2 = (16*(h - z0))/T**2
        b3 = (32*(z0 - h))/T**3
        b4 = (16*(h - z0))/T**4'''
        #---------z calculus------------------------
        z = b4 * (t-ti)**4 + b3 * (t-ti)**3 + b2 * (t-ti)**2 + b1 * (t-ti)**1 + b0
        #---------Parameters of y function-----------
        c0 = y0
        c1 = 0
        c2 = -3 * (y0-y1)/T**2
        c3 = 2 * (y0-y1)/T**3
        
        #---------y calculus------------------------
        #y = self.init[1] #we assume that y is constant 
        y = c3 * (t-ti)**3 + c2 * (t-ti)**2 + c1*(t-ti) + c0
        
        return [x,y,z]

        
# Computes a walking whole-body motion
#
# Input data are
#  - an initial configuration of the robot,
#  - a sequence of step positions (x,y) on the ground
#

def rot_z(theta) : 
    return np.array([np.array([cos(theta), -sin(theta), 0]),
                     np.array([sin(theta), cos(theta), 0]),
                     np.array([0, 0, 1])])

class WalkingMotion(object):
    step_height = 0.05
    single_support_time = .5
    double_support_time = .1
    def __init__(self, robot):
        self.robot = robot

    def compute(self, q0, steps, end, theta):
        # Test input data
        if len(steps) < 4:
            raise RuntimeError("sequence of step should be of length at least 4 instead of " +
                               f"{len(steps)}")
        # Compute offset between waist and center of mass since we control the center of mass
        # indirectly by controlling the waist.
        data = self.robot.model.createData()
        forwardKinematics(self.robot.model, data, q0)
        com = centerOfMass(self.robot.model, data, q0)
        waist_pose = data.oMi[self.robot.waistJointId]
        com_offset = waist_pose.translation - com
        # Trajectory of left and right feet
        self.lf_traj = Piecewise()
        self.rf_traj = Piecewise()
        sst = self.single_support_time
        dst = self.double_support_time
        t = 0
        #initialization 
        
        start_l = data.oMi[self.robot.leftFootJointId].translation
        start_r = data.oMi [self.robot.rightFootJointId].translation
        step_l = steps[1::2]
        step_r = steps[0::2]
        current_l = np.array(start_l)
        current_r = np.array(start_r)


        #add z to steps
        for i in range (len(step_l)) : 
            step_l[i] = np.append(np.array(step_l[i]), start_l[2])
            step_r[i] = np.append(np.array(step_r[i]), start_r[2])


        self.rf_traj.segments.append(Constant(t, t+dst, start_r))
        self.lf_traj.segments.append(Constant(t, t+dst, start_l))

        t = t + dst

        for i in range(len(step_l)) : 
            # on garde current en z pour le assert ligne 45 
            if i != len(step_l) -1 : 
                end_r = np.array(step_r[i+1])
            end_l = np.array(step_l[i])
            
            #left step 
            self.lf_traj.segments.append(SwingFootTrajectory(t,t+sst, current_l, end_l, self.step_height))
            current_l = end_l
            self.rf_traj.segments.append(Constant(t, t+sst, current_r))
        
            t += sst

            #stabilize 
            self.rf_traj.segments.append(Constant(t, t+dst, current_r))
            self.lf_traj.segments.append(Constant(t, t+dst, current_l))

            t += dst
            
            #right step 
            if i != len(step_l) -1 : 
                self.rf_traj.segments.append(SwingFootTrajectory(t,t+sst, current_r, end_r, self.step_height))
            else : 
                self.rf_traj.segments.append(Constant(t,t+sst, current_r))
            current_r = end_r
            self.lf_traj.segments.append(Constant(t, t+sst,current_l))

            t += sst

            #stabilize 
            self.rf_traj.segments.append(Constant(t, t+dst, current_r))
            self.lf_traj.segments.append(Constant(t, t+dst, current_l))

            t += dst
        self.com_trajectory = ComTrajectory(com[0:2], steps, end[0:2], com[2])
        X = self.com_trajectory.compute()
        times = 0.01 * np.arange(len(X)//2)
        #times = 0.01 * np.arange(500)
        com = np.array(list(map(self.com_trajectory, times)))
        rf = np.array(list(map(self.rf_traj, times)))
        lf = np.array(list(map(self.lf_traj, times)))
        configs = []
        cop_des = np.array(list(map(self.com_trajectory.cop_des, times)))
        fig = plt.figure()
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)
        ax1.plot(times, lf[:,0], label="x left foot")
        ax1.plot(times, rf[:,0], label="x right foot")
        ax1.plot(times, cop_des[:,0], label="x CoPdes")
        ax1.legend()
        ax2.plot(times, lf[:,1], label="y left foot")
        ax2.plot(times, rf[:,1], label="y right foot")
        ax2.plot(times, cop_des[:,1], label="y CoPdes")
        ax2.legend()
        ax3.plot(times, lf[:,2], label="z left foot")
        ax3.plot(times, rf[:,2], label="z right foot")
        ax3.legend()
        plt.show()

        div = len(rf) // len(theta)
        i=0
        for t in range(len(rf)) : 

            ik = InverseKinematics (self.robot)
            ik.rightFootRefPose.translation = np.array (rf[t])
            ik.leftFootRefPose.translation = np.array (lf[t])

            ik.waistRefPose.translation = np.array (com[t] + com_offset)

            
            rot = rot_z(theta[i])
            ik.waistRefPose.rotation = rot
            ik.rightFootRefPose.rotation = rot
            ik.leftFootRefPose.rotation = rot

            if  t % div == 0 and i < len(theta)-1: 
                i+=1


            q0 = neutral (robot.model)
            q0 [robot.name_to_config_index["leg_right_4_joint"]] = .2
            q0 [robot.name_to_config_index["leg_left_4_joint"]] = .2
            q0 [robot.name_to_config_index["arm_left_2_joint"]] = .2
            q0 [robot.name_to_config_index["arm_right_2_joint"]] = -.2

            q = ik.solve (q0)
            configs.append(q)

        return configs

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from talos import Robot
    from pinocchio import neutral
    import numpy as np
    from inverse_kinematics import InverseKinematics
    import eigenpy
    from real_trajectory import RealTrajectory

    robot = Robot ()
    
    ik = InverseKinematics (robot)
    ik.rightFootRefPose.translation = np.array ([0, -0.1, 0.1])
    ik.leftFootRefPose.translation = np.array ([0, 0.1, 0.1])
    ik.waistRefPose.translation = np.array ([0, 0, 0.95])

    q0 = neutral (robot.model)
    q0 [robot.name_to_config_index["leg_right_4_joint"]] = .2
    q0 [robot.name_to_config_index["leg_left_4_joint"]] = .2
    q0 [robot.name_to_config_index["arm_left_2_joint"]] = .2
    q0 [robot.name_to_config_index["arm_right_2_joint"]] = -.2
    q = ik.solve (q0)
    robot.display(q[0])
    wm = WalkingMotion(robot)
    # First two values correspond to initial position of feet
    # Last two values correspond to final position of feet
    #steps = [np.array([0, -.1]), np.array([0.4, .1]),
    #         np.array([.8, -.1]), np.array([1.2, .1]),
    #         np.array([1.6, -.1]), np.array([1.6, .1])]


    '''steps = [np.array([0, -.1]), np.array([0.4, .1]),
             np.array([.8, .0]), np.array([1.2, .2]),
             np.array([1.6, .1]), np.array([1.6, .3])]'''


    start = np.array([0,0,0])
    end = np.array([3.2,0.6,0.30])
    rt = RealTrajectory(start, end)
    steps, theta = rt.compute()
    print(steps)
    print(theta)
    configs = wm.compute(q[0], steps, end, theta)
    for q in configs:
        time.sleep(1e-1)
        robot.display(q[0])
    delta_t = wm.com_trajectory.delta_t
    times = delta_t*np.arange(wm.com_trajectory.N+1)
    lf = np.array(list(map(wm.lf_traj, times)))
    rf = np.array(list(map(wm.rf_traj, times)))
    cop_des = np.array(list(map(wm.com_trajectory.cop_des, times)))
    fig = plt.figure()
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)
    ax1.plot(times, lf[:,0], label="x left foot")
    ax1.plot(times, rf[:,0], label="x right foot")
    ax1.plot(times, cop_des[:,0], label="x CoPdes")
    ax1.legend()
    ax2.plot(times, lf[:,1], label="y left foot")
    ax2.plot(times, rf[:,1], label="y right foot")
    ax2.plot(times, cop_des[:,1], label="y CoPdes")
    ax2.legend()
    ax3.plot(times, lf[:,2], label="z left foot")
    ax3.plot(times, rf[:,2], label="z right foot")
    ax3.legend()
    plt.show()

