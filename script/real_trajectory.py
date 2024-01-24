import numpy as np
from numpy.linalg import norm, pinv
from scipy.optimize import fmin_bfgs
import matplotlib.pyplot as plt 



class RealTrajectory(object) : 



    def __init__(self, init, end) : 
        self.init = init
        self.end = end
        self.steps = []
        self.normal_step = 0.5 


    def create_D(self, N) : 
        # Define the 3x3 identity matrix
        I3 = np.identity(3)
        # Initialize the (3N+3) x (3N) rectangular matrix with zeros
        D = np.zeros((3*N + 3, 3*N))
        # Fill the matrix with I3 and -I3 blocks
        for i in range(N):
            # Set the main diagonal blocks to I3
            D[3*i:3*(i+1), 3*i:3*(i+1)] = I3
            # Set the sub-diagonal blocks to -I3
            if i < N - 1:
                D[3*(i+1):3*(i+2), 3*i:3*(i+1)] = -I3
        # Set the last three rows to the last -I3 block
        D[3*N:3*N+3, 3*(N-1):3*N] = -I3

        return np.array(D)

    def compute(self) : 
        dist  = norm(self.init[0:2] - self.end[0:2])

        self.N = round(dist//self.normal_step)+1
        if self.N%2 == 1 : 
            self.N -= 1

        d0 = np.zeros(3*self.N+3)
        d0[0:3] = -self.init    

        d0[-3:] = self.end

        D = self.create_D(self.N)
        X = np.array(pinv(D)@np.transpose(-d0))
        X = np.array([np.array(X[3*i:3*i+3]) for i in range(self.N)])
        steps = np.zeros((len(X)+2, 3))
        steps[0] = self.init
        steps[1:len(X)+1] = X
        steps[-1] = self.end 

        self.steps = steps
        d = [(self.end[0]-self.init[0])/(self.N+1), (self.end[1]-self.init[1])/(self.N+1)]
        print(d)
        com_traj = []
        for i in range(len(steps)-1) :
            if i %2 == 1 : 
                com_traj.append(np.array([steps[i][0], steps[i][1]+0.1]))
            else : 
                com_traj.append(np.array([steps[i][0], steps[i][1]-0.1]))
        com_traj.append(np.array([steps[-1][0], steps[-1][1]]))

        self.com_traj= np.array(com_traj)
        return(com_traj)
        

if __name__ == "__main__":
    start = np.array([0,0,0])
    end = np.array([2,1,0])
    rt = RealTrajectory(start, end)
    rt.compute()
    x = rt.steps[:,0]
    y = rt.steps[:,1]

    x2, y2 = (rt.com_traj[:,0], rt.com_traj[:, 1])
    plt.scatter(x,y)
    plt.scatter(x2,y2)
    plt.show()
     