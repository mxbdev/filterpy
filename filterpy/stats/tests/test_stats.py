# -*- coding: utf-8 -*-
"""Copyright 2015 Roger R Labbe Jr.

FilterPy library.
http://github.com/rlabbe/filterpy

Documentation at:
https://filterpy.readthedocs.org

Supporting book at:
https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python

This is licensed under an MIT license. See the readme.MD file
for more information.
"""

from __future__ import division

from math import exp
import warnings
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import numpy as np
from numpy.linalg import inv
import scipy
from scipy.spatial.distance import mahalanobis as _scipy_mahalanobis
from stats.stats import (norm_cdf,multivariate_gaussian,logpdf,
                            mahalanobis)
from scipy import linalg

ITERS=10000


def scipy_mahalanobis(x,mean,cov):
    # scipy 1.9 will not accept scalars as input, so force the correct
    # behavior so we don't get deprecation warnings or exceptions

    def validate_vector(u):
        u=np.asarray(u).squeeze()
        # Ensure values such as u=1 and u=[1] still return 1-D arrays.
        u=np.atleast_1d(u)
        return u

    x=validate_vector(x)
    mean=validate_vector(mean)
    return _scipy_mahalanobis(x,mean,cov)


def test_mahalanobis():
    global a,b,S
    # int test
    a,b,S=3,1,2
    assert abs(mahalanobis(a,b,S)-scipy_mahalanobis(a,b,1/S))<1.e-12

    # int list
    assert abs(mahalanobis([a],[b],[S])-scipy_mahalanobis(a,b,1/S))<1.e-12
    assert abs(mahalanobis([a],b,S)-scipy_mahalanobis(a,b,1/S))<1.e-12

    # float
    a,b,S=3.123,3.235235,.01234
    assert abs(mahalanobis(a,b,S)-scipy_mahalanobis(a,b,1/S))<1.e-12
    assert abs(mahalanobis([a],[b],[S])-scipy_mahalanobis(a,b,1/S))<1.e-12
    assert abs(mahalanobis([a],b,S)-scipy_mahalanobis(a,b,1/S))<1.e-12

    #float array
    assert abs(mahalanobis(np.array([a]),b,S)-scipy_mahalanobis(a,b,1/S))<1.e-12

    #1d array
    a=np.array([1.,2.])
    b=np.array([1.4,1.2])
    S=np.array([[1.,2.],[2.,4.001]])

    assert abs(mahalanobis(a,b,S)-scipy_mahalanobis(a,b,inv(S)))<1.e-12

    #2d array
    a=np.array([[1.,2.]])
    b=np.array([[1.4,1.2]])
    S=np.array([[1.,2.],[2.,4.001]])

    assert abs(mahalanobis(a,b,S)-scipy_mahalanobis(a,b,inv(S)))<1.e-12
    assert abs(mahalanobis(a.T,b,S)-scipy_mahalanobis(a,b,inv(S)))<1.e-12
    assert abs(mahalanobis(a,b.T,S)-scipy_mahalanobis(a,b,inv(S)))<1.e-12
    assert abs(mahalanobis(a.T,b.T,S)-scipy_mahalanobis(a,b,inv(S)))<1.e-12

    try:
        # mismatched shapes
        mahalanobis([1],b,S)
        assert "didn't catch vectors of different lengths"
    except ValueError:
        pass
    except:
        assert "raised exception other than ValueError"

    # okay, now check for numerical accuracy
    for _ in range(ITERS):
        N=np.random.randint(1,20)
        a=np.random.randn(N)
        b=np.random.randn(N)
        S=np.random.randn(N,N)
        S=np.dot(S,S.T) #ensure positive semi-definite
        assert abs(mahalanobis(a,b,S)-scipy_mahalanobis(a,b,inv(S)))<1.e-12


def test_multivariate_gaussian():

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # test that we treat lists and arrays the same
        mean=(0,0)
        cov=[[1,.5],[.5,1]]
        a=[[multivariate_gaussian((i,j),mean,cov)
              for i in (-1,0,1)]
              for j in (-1,0,1)]

        b=[[multivariate_gaussian((i,j),mean,np.asarray(cov))
              for i in (-1,0,1)]
              for j in (-1,0,1)]

        assert np.allclose(a,b)

        a=[[multivariate_gaussian((i,j),np.asarray(mean),cov)
              for i in (-1,0,1)]
              for j in (-1,0,1)]
        assert np.allclose(a,b)

        try:
            multivariate_gaussian(1,1,-1)
        except:
            pass
        else:
            assert False,"negative variances are meaningless"

        # test that we get the same results as scipy.stats.multivariate_normal
        xs=np.random.randn(1000)
        mean=np.random.randn(1000)
        var=np.random.random(1000)*5

        for x,m,v in zip(xs,mean,var):
            assert abs(multivariate_gaussian(x,m,v)-scipy.stats.multivariate_normal(m,v).pdf(x))<1.e-12


def _is_inside_ellipse(x,y,ex,ey,orientation,width,height):

    co=np.cos(orientation)
    so=np.sin(orientation)

    xx=x*co+y*so
    yy=y*co-x*so

    return (xx/width)**2+(yy/height)**2<=1.


def do_plot_test():
    import matplotlib.pyplot as plt
    from numpy.random import multivariate_normal as mnormal
    from stats.stats import covariance_ellipse,plot_covariance

    p=np.array([[32,15],[15.,40.]])

    x,y=mnormal(mean=(0,0),cov=p,size=5000).T
    sd=2
    a,w,h=covariance_ellipse(p,sd)
    print(np.degrees(a),w,h)

    count=0
    color=[]
    for i in range(len(x)):
        if _is_inside_ellipse(x[i],y[i],0,0,a,w,h):
            color.append('b')
            count+=1
        else:
            color.append('r')
    plt.scatter(x,y,alpha=0.2,c=color)
    plt.axis('equal')

    plot_covariance(mean=(0.,0.),
                    cov=p,
                    std=[1,2,3],
                    alpha=0.3,
                    facecolor='none')

    print(count/len(x))


def test_norm_cdf():
    # test using the 68-95-99.7 rule

    mu=5
    std=3
    var=std*std

    std_1=(norm_cdf((mu-std,mu+std),mu,var))
    assert abs(std_1-.6827)<.0001

    std_1=(norm_cdf((mu+std,mu-std),mu,std=std))
    assert abs(std_1-.6827)<.0001

    std_1half=(norm_cdf((mu+std,mu),mu,var))
    assert abs(std_1half-.6827/2)<.0001

    std_2=(norm_cdf((mu-2*std,mu+2*std),mu,var))
    assert abs(std_2-.9545)<.0001

    std_3=(norm_cdf((mu-3*std,mu+3*std),mu,var))
    assert abs(std_3-.9973)<.0001


def test_logpdf():
    assert 3.9<exp(logpdf(1,1,.01))<4.
    assert 3.9<exp(logpdf([1],[1],.01))<4.
    assert 3.9<exp(logpdf([[1]],[[1]],.01))<4.

    logpdf([1.,2],[1.1,2],cov=np.array([[1.,2],[2,5]]),allow_singular=False)
    logpdf([1.,2],[1.1,2],cov=np.array([[1.,2],[2,5]]),allow_singular=True)


def log_multivariate_normal_density(X,mean,covar,min_covar=1.e-7):
    """Log probability for full covariance matrices. """

    # New BSD License
    #
    # Copyright (c) 2007 - 2012 The scikit-learn developers.
    # All rights reserved.
    #
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:
    #
    #   a. Redistributions of source code must retain the above copyright notice,
    #      this list of conditions and the following disclaimer.
    #   b. Redistributions in binary form must reproduce the above copyright
    #      notice, this list of conditions and the following disclaimer in the
    #      documentation and/or other materials provided with the distribution.
    #   c. Neither the name of the Scikit-learn Developers  nor the names of
    #      its contributors may be used to endorse or promote products
    #      derived from this software without specific prior written
    #      permission.
    #
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    # AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    # ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
    # ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    # DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    # SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    # CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    # LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
    # OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
    # DAMAGE.

    #  taken from scikit-learn

    if hasattr(linalg,'solve_triangular'):
        # only in scipy since 0.9
        solve_triangular=linalg.solve_triangular
    else:
        # slower, but works
        solve_triangular=linalg.solve
    n_dim=X.shape[0]
    mu=mean
    cv=covar

    try:
        cv_chol=linalg.cholesky(cv,lower=True)
    except linalg.LinAlgError:
        # The model is most probabily stuck in a component with too
        # few observations, we need to reinitialize this components
        cv_chol=linalg.cholesky(cv+min_covar*np.eye(n_dim),
                                  lower=True)
    cv_log_det=2*np.sum(np.log(np.diagonal(cv_chol)))
    cv_sol=solve_triangular(cv_chol,(X-mu).T,lower=True).T
    if cv_sol.ndim==1:
        cv_sol=np.expand_dims(cv_sol,axis=0)
    log_prob=-.5*(np.sum(cv_sol**2,axis=1)+\
                                 n_dim*np.log(2*np.pi)+cv_log_det)

    return log_prob


def test_logpdf2():
    z=np.array([1.,2.])
    mean=np.array([1.1,2])
    cov=np.array([[1.,2],[2,5]]);

    p=logpdf(z,mean,cov,allow_singular=False)
    p2=log_multivariate_normal_density(z,mean,cov)
    print('p',p)
    print('p2',p2)
    print('p-p2',p-p2)


def covariance_3d_plot_test():
    import matplotlib.pyplot as plt
    from stats.stats import plot_3d_covariance

    mu=[13456.3,2320,672.5]

    C=np.array([[1.0,.03,.2],
                  [.03,4.0,.0],
                  [.2,.0,16.1]])

    sample=np.random.multivariate_normal(mu,C,size=1000)

    fig=plt.gcf()
    ax=fig.add_subplot(111,projection='3d')
    ax.scatter(xs=sample[:,0],ys=sample[:,1],zs=sample[:,2],s=1)
    plot_3d_covariance(mu,C,alpha=.4,std=3,limit_xyz=True,ax=ax)


if __name__=="__main__":
    test_multivariate_gaussian()
    test_mahalanobis()
    test_logpdf2()
    covariance_3d_plot_test()
    plt.figure()
    do_plot_test()
