import numpy as np
from numpy.linalg import norm, pinv
from scipy.optimize import fmin_bfgs




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
        N = round(dist//self.normal_step)

        d0 = np.zeros(3*N+3)
        d0[0:3] = -self.init    

        d0[-3:] = self.end

        D = self.create_D(N)
        X = pinv(D)@np.transpose(-d0)
        X = [X[i:i+3] for i in range(len(X)//3)]

        print(X)

if __name__ == "__main__":
    rt = RealTrajectory(np.array([0,0,0]), np.array([1,1,0]))
    rt.compute()