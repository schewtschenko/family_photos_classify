CREATE TABLE camera (
  id    int4 NOT NULL, 
  model varchar(30) NOT NULL UNIQUE, 
  brand varchar(30), 
  CONSTRAINT camera_pkey 
    PRIMARY KEY (id));
CREATE TABLE city (
  id   int4 NOT NULL, 
  name varchar(255) NOT NULL UNIQUE, 
  CONSTRAINT city_pkey 
    PRIMARY KEY (id));
CREATE TABLE country (
  id   int4 NOT NULL, 
  name varchar(255) NOT NULL UNIQUE, 
  CONSTRAINT country_pkey 
    PRIMARY KEY (id));
CREATE TABLE image (
  id           int4 NOT NULL, 
  res_width    int4 NOT NULL, 
  res_height   int4 NOT NULL, 
  subfolder_id int4 NOT NULL, 
  file_name    varchar(255) NOT NULL, 
  photo_time   timestamp, 
  camera_id    int4 NOT NULL, 
  CONSTRAINT image_pkey 
    PRIMARY KEY (id), 
  CONSTRAINT image_file_path_uniq 
    UNIQUE (subfolder_id, file_name));
CREATE TABLE image_location (
  image_id    int4 NOT NULL, 
  location_id int4 NOT NULL, 
  gnss_pos    char(1) NOT NULL, 
  latitude    numeric(10, 5) NOT NULL, 
  longitude   numeric(10, 5) NOT NULL, 
  CONSTRAINT image_location_pkey 
    PRIMARY KEY (image_id), 
  CONSTRAINT gnss_pos_check 
    CHECK (gnss_pos in ('Y','N')));
CREATE TABLE location (
  id         int4 NOT NULL, 
  place      varchar(255) NOT NULL UNIQUE, 
  country_id int4 NOT NULL, 
  region_id  int4 NOT NULL, 
  city_id    int4 NOT NULL, 
  latitude   numeric(10, 5) NOT NULL, 
  longitude  numeric(10, 5) NOT NULL, 
  CONSTRAINT location_desc_pkey 
    PRIMARY KEY (id));
CREATE TABLE region (
  id   int4 NOT NULL, 
  name varchar(255) NOT NULL UNIQUE, 
  CONSTRAINT region_pkey 
    PRIMARY KEY (id));
CREATE TABLE subfolder (
  id   int4 NOT NULL, 
  name varchar(255) NOT NULL UNIQUE, 
  CONSTRAINT subfolder_pkey 
    PRIMARY KEY (id));
ALTER TABLE image ADD CONSTRAINT image_camera_id_fkey FOREIGN KEY (camera_id) REFERENCES camera (id);
ALTER TABLE image_location ADD CONSTRAINT image_location_image_id_fkey FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE Cascade;
ALTER TABLE image_location ADD CONSTRAINT image_location_location_id_fkey FOREIGN KEY (location_id) REFERENCES location (id);
ALTER TABLE image ADD CONSTRAINT image_subfolder_id_fkey FOREIGN KEY (subfolder_id) REFERENCES subfolder (id);
ALTER TABLE location ADD CONSTRAINT location_city_id FOREIGN KEY (city_id) REFERENCES city (id);
ALTER TABLE location ADD CONSTRAINT location_country_id_fkey FOREIGN KEY (country_id) REFERENCES country (id);
ALTER TABLE location ADD CONSTRAINT location_region_id_fkey FOREIGN KEY (region_id) REFERENCES region (id);


