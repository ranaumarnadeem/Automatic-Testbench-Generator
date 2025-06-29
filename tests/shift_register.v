module counter4 (
    input clk,
    input rst,
    input [3:0] en,
    output reg [3:0] out
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            out <= 0;
        else if (en)
            out <= out + 1;
    end
endmodule


// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module counter4_tb;
    // Declare regs for inputs and wires for outputs
    reg clk;
    reg rst;
  reg [3:0] en;
  wire [3:0] out;

    // Instantiate the DUT
    counter4 uut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .out(out)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Reset sequence
    initial begin
        rst = 1;
        #10;
        rst = 0;
    end

    // Input stimulus
    initial begin
        en = 0;
        #10;
        rst = 0;
        en = 0;
        #10;
        rst = 0;
        en = 1;
        #10;
        rst = 0;
        en = 2;
        #10;
        rst = 0;
        en = 3;
        #10;
        rst = 0;
        en = 4;
        #10;
        rst = 0;
        en = 5;
        #10;
        rst = 0;
        en = 6;
        #10;
        rst = 0;
        en = 7;
        #10;
        rst = 0;
        en = 8;
        #10;
        rst = 0;
        en = 9;
        #10;
        rst = 0;
        en = 10;
        #10;
        rst = 0;
        en = 11;
        #10;
        rst = 0;
        en = 12;
        #10;
        rst = 0;
        en = 13;
        #10;
        rst = 0;
        en = 14;
        #10;
        rst = 0;
        en = 15;
        #10;
        rst = 1;
        en = 0;
        #10;
        rst = 1;
        en = 1;
        #10;
        rst = 1;
        en = 2;
        #10;
        rst = 1;
        en = 3;
        #10;
        rst = 1;
        en = 4;
        #10;
        rst = 1;
        en = 5;
        #10;
        rst = 1;
        en = 6;
        #10;
        rst = 1;
        en = 7;
        #10;
        rst = 1;
        en = 8;
        #10;
        rst = 1;
        en = 9;
        #10;
        rst = 1;
        en = 10;
        #10;
        rst = 1;
        en = 11;
        #10;
        rst = 1;
        en = 12;
        #10;
        rst = 1;
        en = 13;
        #10;
        rst = 1;
        en = 14;
        #10;
        rst = 1;
        en = 15;
        #10;
        $finish;
    end
endmodule