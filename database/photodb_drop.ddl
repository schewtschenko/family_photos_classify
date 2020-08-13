ALTER TABLE gps_location DROP FOREIGN KEY gps_location_image_id_fkey;
ALTER TABLE image DROP FOREIGN KEY image_camera_id_fkey;
ALTER TABLE image DROP FOREIGN KEY image_subfolder_id_fkey;
DROP TABLE IF EXISTS camera;
DROP TABLE IF EXISTS gps_location;
DROP TABLE IF EXISTS image;
DROP TABLE IF EXISTS subfolder;

