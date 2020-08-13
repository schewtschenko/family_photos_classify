CREATE TABLE camera (
  id    int(10) NOT NULL, 
  model varchar(30) NOT NULL UNIQUE, 
  brand varchar(30), 
  CONSTRAINT camera_pkey 
    PRIMARY KEY (id));
CREATE TABLE gps_location (
  image_id  int(10) NOT NULL, 
  latitude  numeric(10, 5) NOT NULL, 
  longitude numeric(10, 5) NOT NULL, 
  CONSTRAINT gps_location_pkey 
    PRIMARY KEY (image_id));
CREATE TABLE image (
  id                int(10) NOT NULL, 
  resolution_width  int(10) NOT NULL, 
  resolution_height int(10) NOT NULL, 
  subfolder_id      int(10) NOT NULL, 
  file_name         varchar(255) NOT NULL, 
  photo_time        datetime NULL, 
  camera_id         int(10) NOT NULL, 
  CONSTRAINT image_pkey 
    PRIMARY KEY (id), 
  CONSTRAINT image_file_path_uniq 
    UNIQUE (subfolder_id, file_name));
CREATE TABLE subfolder (
  id   int(10) NOT NULL, 
  name varchar(255) NOT NULL UNIQUE, 
  CONSTRAINT subfolder_pkey 
    PRIMARY KEY (id));
ALTER TABLE gps_location ADD CONSTRAINT gps_location_image_id_fkey FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE Cascade;
ALTER TABLE image ADD CONSTRAINT image_camera_id_fkey FOREIGN KEY (camera_id) REFERENCES camera (id);
ALTER TABLE image ADD CONSTRAINT image_subfolder_id_fkey FOREIGN KEY (subfolder_id) REFERENCES subfolder (id);

