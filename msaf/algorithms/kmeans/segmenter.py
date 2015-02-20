#!/usr/bin/env python
# coding: utf-8
"""
This script identifies the boundaries of a given track using an unpublished
k-means method.

"""

__author__ = "Oriol Nieto"
__copyright__ = "Copyright 2014, Music and Audio Research Lab (MARL)"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "oriol@nyu.edu"

import argparse
import logging
import numpy as np
import time
from scipy.spatial import distance
from scipy.ndimage import filters
from scipy.cluster.vq import whiten, vq, kmeans
import sys
import pylab as plt

sys.path.append("../../")
import msaf_io as MSAF
import utils as U


def median_filter(X, M=8):
    """Median filter along the first axis of the feature matrix X."""
    for i in xrange(X.shape[1]):
        X[:, i] = filters.median_filter(X[:, i], size=M)
    return X


def mean_filter(x, M=9):
    """Average filter."""
    #window = np.ones(M) / float(M)
    window = np.hanning(M)
    return np.convolve(x, window, 'same')


def compute_ssm(X, metric="seuclidean"):
    """Computes the self-similarity matrix of X."""
    D = distance.pdist(X, metric=metric)
    D = distance.squareform(D)
    D /= D.max()
    return 1 - D


def compute_nc(X, G):
    """Computes the novelty curve from the self-similarity matrix X and
        the gaussian kernel G."""
    N = X.shape[0]
    M = G.shape[0]
    nc = np.zeros(N)

    for i in xrange(M / 2, N - M / 2 + 1):
        nc[i] = np.sum(X[i - M / 2:i + M / 2, i - M / 2:i + M / 2] * G)

    # Normalize
    nc += nc.min()
    nc /= nc.max()
    return nc


def pick_peaks(nc, L=16):
    """Obtain peaks from a novelty curve using an adaptive threshold."""
    offset = nc.mean() / 2.
    th = filters.median_filter(nc, size=L) + offset
    #th = filters.gaussian_filter(nc, sigma=L/2., mode="nearest") + offset
    peaks = []

    k_hill = 0
    hill = False
    for i in xrange(1, nc.shape[0] - 1):
        # is it above the threshold?
        if nc[i] > th[i]:
            # is it a peak?
            if nc[i - 1] < nc[i] and nc[i] > nc[i + 1]:
                    k_hill = 0
                    hill = False
                    peaks.append(i)
            # is it a flat hill?
            if nc[i - 1] == nc[i] and nc[i] == nc[i - 1]:
                hill = True
                k_hill += 1
        elif hill:
            peaks.append(i - k_hill / 2)
            k_hill = 0
            hill = False

    #plt.plot(nc)
    #plt.plot(th)
    #plt.show()
    #print peaks

    return peaks


def get_boundaries(S, convex, rank, niter=500):
    """
    Gets the boundaries from the factorization matrices.

    Parameters
    ----------
    S: np.array()
        Self-similarity matrix
    convex: boolean
        Whether to use convex or standard nmf
    rank: int
        Rank of decomposition
    niter: int
        Number of iterations for k-means

    Returns
    -------
    bounds_idx: np.array
        Bound indeces found
    """
    M = 9   # Size of the mean filter to compute the novelty curve
    L = 15   # Size of the peak picking filter

    # Find non filtered boundaries
    bound_idxs = np.empty(0)
    while True:
        codebook, dist = kmeans(S, rank, iter=niter)
        codes, disto = vq(S, codebook)

        # Find points where there's a cluster difference (boundary)
        b = np.where(np.diff(codes) != 0)[0] + 1
        bound_idxs = np.concatenate((bound_idxs, b))

        # Increase rank if we found too few boundaries
        if len(np.unique(bound_idxs)) <= 2:
            bound_idxs = np.empty(0)
            rank += 1
        else:
            break

    # Compute novelty curve from initial boundaries
    nc = np.zeros(S.shape[0])
    for b in bound_idxs:
        nc[int(b)] += 1
    nc = mean_filter(nc, M=M)
    #plt.plot(nc); plt.show()

    # Pick peaks to obtain the best boundaries (filtered boundaries)
    bound_idxs = pick_peaks(nc, L=L)

    return bound_idxs


def process(in_path, feature="hpcp", annot_beats=False):
    """Main process."""

    # C-NMF params
    m = 13          # Size of median filter
    rank = 3        # Rank of decomposition
    niter = 300     # Iterations for the matrix factorization and clustering
    convex = True   # Use convex or standard NMF
    dist = "correlation"

    # Read features
    chroma, mfcc, beats, dur = MSAF.get_features(in_path,
                                                 annot_beats=annot_beats)

    # Use specific feature
    if feature == "hpcp":
        F = U.lognormalize_chroma(chroma)  # Normalize chromas
    elif "mfcc":
        F = mfcc
    else:
        logging.error("Feature type not recognized: %s" % feature)

    if F.shape[0] >= m:
        # Median filter
        F = median_filter(F, M=m)
        #plt.imshow(F.T, interpolation="nearest", aspect="auto"); plt.show()

        # Self similarity matrix
        S = compute_ssm(F, metric=dist)
        #plt.imshow(S, interpolation="nearest", aspect="auto"); plt.show()

        # Find the boundary indices using matrix factorization
        bound_idxs = get_boundaries(S, convex, rank, niter=niter)
    else:
        # The track is too short. We will only output the first and last
        # time stamps
        bound_idxs = np.empty(0)

    # Concatenate first boundary
    bound_idxs = np.concatenate(([0], bound_idxs)).astype(int)

    # Read annotated bounds for comparison purposes
    #ann_bounds = MSAF.read_annot_bound_frames(in_path, beats)
    #logging.info("Annotated bounds: %s" % ann_bounds)
    #logging.info("Estimated bounds: %s" % bound_idxs)

    # Get times
    est_times = beats[bound_idxs]

    # Concatenate last boundary
    est_times = np.concatenate((est_times, [dur]))

    # Concatenate last boundary
    logging.info("Estimated times: %s" % est_times)

    return est_times


def main():
    """Main function to parse the arguments and call the main process."""
    parser = argparse.ArgumentParser(description=
        "Segments the given audio file using the k-means method.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_path",
                        action="store",
                        help="Input path to the audio file")
    parser.add_argument("-f",
                        action="store",
                        dest="feature",
                        help="Feature to use (mfcc or hpcp)",
                        default="hpcp")
    parser.add_argument("-b",
                        action="store_true",
                        dest="annot_beats",
                        help="Use annotated beats",
                        default=False)
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
        level=logging.INFO)

    # Run the algorithm
    process(args.in_path, feature=args.feature, annot_beats=args.annot_beats)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))

if __name__ == '__main__':
    main()
