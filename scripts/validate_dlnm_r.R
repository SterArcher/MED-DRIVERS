# Validate the Python DLNM (notebooks/03_2_dlnm.ipynb) against the R package dlnm.
#
# For each primary analysis (TEMP, ILI, PM10, PM25; one <ID>_meta.json per model), the notebook exports:
#   <H>_data.csv   date, y (outcome, in-sample days only), in_sample (0/1), x (exposure on the analysis scale,
#                  all days, so lags have their history), temp (for the temperature cross-basis of PM10 and PM25),
#                  z0, z1, ... (all non-exposure columns of the Python design: time spline, adjustments,
#                  day of week, residual term), in-sample days only
#   <ID>_meta.json  bases (knots, lag range), prediction values (at) and centring value (cen)
#   <ID>_python.csv the Python predictions
# This script builds the cross-basis independently with dlnm::crossbasis, fits the same quasi-Poisson model
# with glm, and writes <ID>_r.csv with the cumulative log-RR (dlnm::crosspred), its SE, the Wald F
# statistic of the cross-basis and its p-value.
#
# Usage: Rscript scripts/validate_dlnm_r.R outputs/03_2_dlnm/r_validation
# Requires: install.packages(c("dlnm", "jsonlite"))

suppressPackageStartupMessages({
  library(dlnm)
  library(splines)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
dir <- if (length(args) >= 1) args[1] else "outputs/03_2_dlnm/r_validation"

hyps <- sub("_meta\\.json$", "", list.files(dir, pattern = "_meta\\.json$"))
for (h in hyps) {
  d <- read.csv(file.path(dir, paste0(h, "_data.csv")))
  meta <- fromJSON(file.path(dir, paste0(h, "_meta.json")))

  argvar <- if (meta$exp_basis == "ns") {
    list(fun = "ns", knots = meta$var_knots, Boundary.knots = meta$var_range)
  } else {
    list(fun = "lin")
  }
  arglag <- if (meta$lag_basis == "integer") {
    list(fun = "integer")
  } else {
    list(fun = "ns", knots = logknots(meta$lag_max, meta$lag_nk))
  }
  cb <- crossbasis(d$x, lag = meta$lag_max, argvar = argvar, arglag = arglag)

  s <- d$in_sample == 1
  Z <- as.matrix(d[s, grep("^z[0-9]+$", names(d))])
  X <- cbind(cb[s, , drop = FALSE], Z)
  if (isTRUE(meta$temp_cb)) {
    cbt <- crossbasis(d$temp, lag = 21,
                      argvar = list(fun = "ns", knots = meta$temp_knots, Boundary.knots = meta$temp_range),
                      arglag = list(fun = "ns", knots = logknots(21, 3)))
    X <- cbind(X, cbt[s, , drop = FALSE])
  }
  y <- d$y[s]
  fit <- glm(y ~ X, family = quasipoisson())

  ind <- 1 + seq_len(ncol(cb))                       # cross-basis coefficients follow the intercept
  b <- coef(fit)[ind]
  V <- vcov(fit)[ind, ind]
  if (anyNA(b)) stop(h, ": aliased cross-basis coefficients in R")
  cp <- crosspred(cb, coef = b, vcov = V, model.link = "log", at = meta$at, cen = meta$cen)
  F <- as.numeric(t(b) %*% solve(V, b)) / length(b)
  p <- pf(F, length(b), df.residual(fit), lower.tail = FALSE)

  out <- data.frame(at = meta$at, logRR_r = as.numeric(cp$allfit), se_r = as.numeric(cp$allse), F_r = F, p_r = p)
  write.csv(out, file.path(dir, paste0(h, "_r.csv")), row.names = FALSE)
  cat(sprintf("%s: n = %d, %d cross-basis terms, dispersion %.3f, F = %.4f\n",
              h, sum(s), length(b), summary(fit)$dispersion, F))
}
cat("R", R.version$major, ".", R.version$minor, "| dlnm", as.character(packageVersion("dlnm")), "\n")
