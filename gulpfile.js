/*
* Copyright (C) 2025 Entidad Pública Empresarial Red.es
*
* This file is part of "comments (datos.gob.es)".
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 2 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

const { watch, src, dest } = require("gulp");

const if_ = require("gulp-if");
const sourcemaps = require("gulp-sourcemaps");
const less = require("gulp-less");
const { resolve } = require("path");

const isDev = () => !!process.env.DEBUG;
const lessFolder = "ckanext/comments/assets/less";
const cssFolder = "ckanext/comments/assets/css";

const buildTask = () =>
  src([resolve(__dirname, lessFolder, "comments-thread.less")])
    .pipe(if_(isDev, sourcemaps.init()))
    .pipe(less())
    .pipe(if_(isDev, sourcemaps.write()))
    .pipe(dest(resolve(__dirname, cssFolder)));

const watchTask = () =>
  watch(
    resolve(__dirname, lessFolder, "*.less"),
    { ignoreInitial: false },
    buildTask
  );

exports.build = buildTask;
exports.watch = watchTask;
